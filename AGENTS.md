# Hướng dẫn cho agent

Đọc README.md, docs/RESEARCH_STATE.md, docs/NEXT_EXPERIMENTS.md, prompts/ASTRA_NEXT_RUN.md. User instruction mới rõ ràng có thể thay hướng nhưng phải ghi decision; không viết lại kết quả cũ.

Current direction: crossed forecaster-selector evaluation, OIC/independent-split baseline, then temporal and official-market validation. Historical + SE penalty is a selector using the same historical forecast surface. Own-selected error does not prove a better forecaster. No APTC v3 or neural sweep before these gates.

Do not alter measured v1/v2 package files, configs, reports, raw archives or importer checksums just to make new code pass. Replays use detached historical worktree or isolated work directory. Some imported artifacts are absent from main: mark MISSING/NOT_RUN, do not invent them.

New code/config/output go to a research branch and separate run directories. No force-push main, no overwrite of local uncommitted work. No new raw market/credential/cache commits without use-rights review. Keep all negative results and source citations.

Separate forecast on common targets, selected decision quality and reserve utility. Distinguish observation date, publication time, gap, stride and holding horizon. One realized loss is not ES truth. Portfolio bank samples are not independent market observations. Markov latent-state oracle is not equally informed model evidence.

OIC requires an applicability audit; don't label a generic SE penalty OIC. Do not fabricate coherent VaR/ES pairs by adding arbitrary optimism correction. Data provider/use terms must be checked on actual download. ECB FX is reference-factor data, not executable PnL.

Progress logs/tqdm/ETA, actual timings and warnings stay in runs/, not endless docs/README appendices. Multiprocessing is not independent subagent review. Report VERIFIED/REPORTED/PROPOSED/NOT_RUN separately.
