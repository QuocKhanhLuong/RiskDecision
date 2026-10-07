"""Simulation and parameter-oracle evaluation only; never imported by models."""
import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal


def parameters(cfg):
    d=cfg['dgp'];sd=np.asarray(d['std']);mu=np.asarray(d['means'])
    cov=np.outer(sd,sd)*(d['correlation']*np.ones((len(sd),len(sd)))+(1-d['correlation'])*np.eye(len(sd)))
    return mu,cov,np.array([mu,mu+d['high_mean_shift']]),np.array([cov,cov*d['high_scale']**2])


def transition(world,t,cfg):
    key='transition1' if world=='markov_shift' and t>=cfg['dgp']['shift_time'] else 'transition0'
    return np.asarray(cfg['dgp'][key])


def stationary_prob(p):
    return np.array([p[1,0],p[0,1]])/(p[1,0]+p[0,1])


def marginal_probs(world,length,cfg):
    prob=stationary_prob(transition(world,0,cfg));rows=[]
    for t in range(length):
        prob=prob@transition(world,t,cfg);rows.append(prob.copy())
    return np.array(rows)


def generate(seed,cfg):
    length=max(cfg['origins'])+1;dim=cfg['dgp']['dim'];rng=np.random.default_rng(seed)
    z=rng.normal(size=(length+1,dim));uniform=rng.uniform(size=length+1)
    mu,cov,emission_mu,emission_cov=parameters(cfg);chol=np.linalg.cholesky(cov)
    phi=cfg['dgp']['phi'];previous=mu+chol@z[0];ar=[]
    for t in range(length):
        previous=mu+phi*(previous-mu)+np.sqrt(1-phi**2)*(chol@z[t+1]);ar.append(previous.copy())
    result={'ar1_stationary':{'returns':np.array(ar),'states':np.full(length,-1,dtype=int)}}
    initial=int(uniform[0]>stationary_prob(transition('markov_stationary',0,cfg))[0])
    for world in ['markov_stationary','markov_shift']:
        state=initial;xs=[];states=[]
        for t in range(length):
            state=int(uniform[t+1]>transition(world,t,cfg)[state,0])
            xs.append(emission_mu[state]+(chol@z[t+1])*(1 if state==0 else cfg['dgp']['high_scale']))
            states.append(state)
        result[world]={'returns':np.array(xs),'states':np.array(states)}
    return result


def filtered_next(past,world,start,cfg):
    """Only the permitted observed window; true parameters, no latent states."""
    _,_,mu,cov=parameters(cfg)
    prior=marginal_probs(world,start+1,cfg)[start]
    logpdf=np.column_stack([multivariate_normal.logpdf(past,mean=mu[k],cov=cov[k]) for k in range(2)])
    for offset,row in enumerate(logpdf):
        logpost=np.log(prior)+row;post=np.exp(logpost-logsumexp(logpost))
        prior=post@transition(world,start+offset+1,cfg)
    return prior


def laws(past,world,origin,cfg,fit_n,last_state):
    """Targets after fitting; latent reference is separate from the observed target."""
    mu,cov,emission_mu,emission_cov=parameters(cfg)
    if world=='ar1_stationary':
        phi=cfg['dgp']['phi']
        conditional={'p':np.ones(1),'mu':(mu+phi*(past[-1]-mu))[None,:],'cov':((1-phi**2)*cov)[None,:,:]}
        marginal={'p':np.ones(1),'mu':mu[None,:],'cov':cov[None,:,:]}
        return conditional,marginal,None
    start=origin-len(past)
    weights=filtered_next(past,world,start,cfg)
    conditional={'p':weights,'mu':emission_mu,'cov':emission_cov}
    marginal={'p':marginal_probs(world,origin,cfg)[start:start+fit_n].mean(axis=0),'mu':emission_mu,'cov':emission_cov}
    latent={'p':transition(world,origin,cfg)[last_state],'mu':emission_mu,'cov':emission_cov}
    return conditional,marginal,latent
