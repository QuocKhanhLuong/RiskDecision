"""Fresh generators, observed-context posterior fit, frozen policy ablations."""
import hashlib

import numpy as np
from scipy.special import softmax
from scipy.stats import beta

from .core import endpoint_regrets, make_bank, risk_extrema, solve_local, solve_worlds


def seed(config, name):
    return int.from_bytes(hashlib.sha256(f"{config['seed_namespace']}/{name}".encode()).digest()[:8], 'big')


def arrays_hash(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


def observed_posterior_seed(config, z, categories, design):
    """Identical observations/public design imply identical randomized stress policy."""
    observed = arrays_hash(z, categories, design['loss_matrix'], design['weights'])
    return seed(config, f'observed-posterior-{observed}')


def public_design(config):
    rng = np.random.default_rng(seed(config, 'public-design'))
    n, d = config['policy_atoms'], config['policy_assets']
    common, sector = rng.normal(size=(2, n))
    sign = np.r_[np.ones(d//2), -np.ones(d-d//2)]
    asset_losses = .01*(.3*common[:, None]+sector[:, None]*sign+.3*rng.normal(size=(n, d)))
    weights = [np.full(d, 1/d)]
    for i in range(d):
        for j in range(i):
            w = np.zeros(d)
            w[i] = w[j] = .5
            weights.append(w)
    while len(weights) < config['policy_bank_size']:
        w = rng.dirichlet(np.full(d, 3.))
        if w.max() <= .5:
            weights.append(w)
    weights = np.array(weights[:config['policy_bank_size']])
    return {'asset_losses': asset_losses, 'sector': sector, 'weights': weights,
            'loss_matrix': asset_losses@weights.T}


def generate_history(config, design, family, index, development=False):
    """Evaluator owns truth. Only observed z/category history passes to fit()."""
    prefix = 'development' if development else 'policy'
    case_seed = seed(config, f'{prefix}-{family}-{index}')
    rng = np.random.default_rng(case_seed)
    transition = np.array([[.94, .06], [.12, .88]])
    components = np.array([softmax(-1.5*design['sector']), softmax(1.5*design['sector'])])
    t = config['policy_window']
    z = np.empty(t, int)
    categories = np.empty(t, int)
    z[0] = rng.choice(2, p=[2/3, 1/3])
    for j in range(t):
        if j:
            z[j] = rng.choice(2, p=transition[z[j-1]])
        shifted = family == 'component_shift' and j >= config['shift_at']
        emissions = components[::-1] if shifted else components
        categories[j] = rng.choice(config['policy_atoms'], p=emissions[z[j]])
    current = components[::-1] if family == 'component_shift' else components
    return {'seed': case_seed, 'z': z, 'categories': categories,
            'truth': {'components': current, 'q': transition[z[-1], 1]}}


def fit_observed(config, z, categories, posterior_seed):
    """No family, true probability or future outcomes accepted by this API."""
    z, categories = np.asarray(z), np.asarray(categories)
    if z.shape != (config['policy_window'],) or categories.shape != z.shape:
        raise ValueError('exact shared history window required')
    if (z < 0).any() or (z > 1).any() or (categories < 0).any() or (categories >= config['policy_atoms']).any():
        raise ValueError('invalid observed context/category')
    emissions = np.full((2, config['policy_atoms']), config['emission_prior_per_atom'], float)
    transition = np.full((2, 2), config['transition_prior_per_outcome'], float)
    np.add.at(emissions, (z, categories), 1)
    np.add.at(transition, (z[:-1], z[1:]), 1)
    last = int(z[-1])
    a, b = transition[last, 1], transition[last, 0]
    q_mean = float(a/(a+b))
    interval = beta.ppf(config['q_posterior_quantiles'], a, b).tolist()
    nominal = emissions/emissions.sum(axis=1, keepdims=True)
    rng = np.random.default_rng(posterior_seed)
    worlds = [nominal]
    worlds += [np.array([rng.dirichlet(row) for row in emissions]) for _ in range(config['posterior_draw_worlds'])]
    return {'worlds': [p.tolist() for p in worlds], 'q_mean': q_mean, 'interval': interval,
            'emission_counts_plus_prior': emissions.tolist(),
            'transition_counts_plus_prior': transition.tolist(), 'last_context': last,
            'posterior_seed': posterior_seed,
            'scope': 'finite posterior stress worlds; no simultaneous true-law coverage guarantee'}


def choose_policies(config, design, fit, categories):
    x, weights = design['loss_matrix'], design['weights']
    costs = config['switch_cost_per_turnover']*.5*np.abs(weights-weights[0]).sum(axis=1)
    worlds = [make_bank(x, p, config['policy_alpha']) for p in fit['worlds']]
    intervals = [fit['interval']]*len(worlds)
    exact = solve_worlds(worlds, costs, intervals)
    shared_end = np.max([endpoint_regrets(w, costs, q) for w, q in zip(worlds, intervals)], axis=0)
    extrema = [risk_extrema(w, costs, q) for w, q in zip(worlds, intervals)]
    extrema_end = [risk_extrema(w, costs, q, True) for w, q in zip(worlds, intervals)]
    low, high = np.min([s[0] for s in extrema], axis=0), np.max([s[1] for s in extrema], axis=0)
    low_end, high_end = np.min([s[0] for s in extrema_end], axis=0), np.max([s[1] for s in extrema_end], axis=0)
    rectangular = high-low.min()
    rectangular_end = high_end-low_end.min()
    nominal = solve_local(worlds[0], costs, fit['interval'])
    fixed_q = solve_worlds(worlds, costs, [[fit['q_mean']]*2]*len(worlds))
    no_cost = solve_worlds(worlds, np.zeros(len(costs)), intervals)
    forecast = np.array([law.es(fit['q_mean']) for law in worlds[0]])
    empirical = np.bincount(categories, minlength=config['policy_atoms']).astype(float)/len(categories)
    historical = np.array([law.es(0) for law in make_bank(x, [empirical, empirical], config['policy_alpha'])])
    selected = {'point': int(np.argmin(forecast+costs)), 'shared_full': exact['selected'],
                'shared_endpoints': int(np.argmin(shared_end)),
                'rectangular_full': int(np.argmin(rectangular)),
                'rectangular_endpoints': int(np.argmin(rectangular_end)),
                'nominal_components': nominal['selected'], 'fixed_q': fixed_q['selected'],
                'ignore_cost': no_cost['selected'], 'historical': int(np.argmin(historical+costs)),
                'incumbent': 0}
    # The rectangular objective differs from absolute worst-case ES by one constant.
    assert selected['rectangular_full'] == int(np.argmin(high))
    return {'selected': selected, 'costs': costs.tolist(), 'nominal_forecast': forecast.tolist(),
            'historical_forecast': historical.tolist(), 'shared_certificate': exact,
            'regret_surfaces': {'shared_full': exact['regrets'], 'shared_endpoints': shared_end.tolist(),
                                'rectangular_full': rectangular.tolist(),
                                'rectangular_endpoints': rectangular_end.tolist()},
            'one_common_nominal_forecast_for_same_fit_policies': True}


def evaluate(config, design, decision, truth):
    """Truth enters after decisions are locked; no future realized loss used as ES truth."""
    laws = make_bank(design['loss_matrix'], truth['components'], config['policy_alpha'])
    risk = np.array([law.es(truth['q']) for law in laws])
    costs = np.array(decision['costs'])
    net = risk+costs
    regret = net-net.min()
    metrics = {}
    for name, j in decision['selected'].items():
        metrics[name] = {'index': j, 'true_es': float(risk[j]), 'cost': float(costs[j]),
                         'true_net_risk': float(net[j]), 'true_net_regret': float(regret[j]),
                         'switched': j != 0, 'harmful_switch': bool(net[j] > net[0]+config['numeric_atol'])}
    j = decision['selected']['shared_full']
    bound = decision['shared_certificate']['regrets'][j]
    return {'policies': metrics, 'true_risks': risk.tolist(), 'true_net_regrets': regret.tolist(),
            'same_target_forecast_mse': float(np.mean((np.array(decision['nominal_forecast'])-risk)**2)),
            'historical_same_target_forecast_mse': float(np.mean((np.array(decision['historical_forecast'])-risk)**2)),
            'stress_bound_underestimates_true_regret': bool(regret[j] > bound+config['numeric_atol']),
            'true_minus_stress_regret_bound': float(regret[j]-bound)}
