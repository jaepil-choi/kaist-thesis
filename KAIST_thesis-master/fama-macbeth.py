# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: sandbox312
#     language: python
#     name: python3
# ---

# %% [markdown]
# ## Fama Macbeth Regression

# %%
import wrds
import pandas as pd
import numpy as np

from statsmodels.regression.rolling import RollingOLS
import statsmodels.formula.api as smf
import scipy.stats as stats

import linearmodels as lm

# %% [markdown]
# ## 어지원 조교님 세션

# %% [markdown]
# ### Load FF tables

# %%
db = wrds.Connection(
    wrds_username="jaewrdskaist",
    wrds_password="hisoWRDS23@#"
)

# %%
db.list_tables(library='ff')

# %% [markdown]
# ### 25 size, value vw portfolios

# %%
portfolio = db.get_table(table='portfolios25', library='ff')
portfolio = portfolio[3:]

# %%
portfolio['date'] = pd.to_datetime(portfolio['date'], format='%Y-%m-%d')
date = portfolio['date'] - pd.tseries.offsets.MonthEnd()
portfolio = portfolio.iloc[:, 0:25]

# %%
date

# %%
portfolio['date'] = date

# %%
portfolio = pd.melt(portfolio, id_vars=['date'])

# %% [markdown]
# ### Monthly FF3 Factors & Risk Free Rate

# %%
monthlyff = db.get_table(table='factors_monthly', library='ff')[['date', 'mktrf', 'hml', 'smb', 'rf']]
monthlyff['date'] = pd.to_datetime(monthlyff['date'], format='%Y-%m-%d')
monthlyff['date'] = monthlyff['date'] - pd.tseries.offsets.MonthEnd()

# %%
portfolio.dropna(subset=['date'], inplace=True)

# %% [markdown]
# ### Final Dataset

# %%
data = pd.merge(portfolio, monthlyff, on='date', how='left')
data['exret'] = data['value'] - data['rf']

# %%
data.head()

# %% [markdown]
# ## Method 1. 조교님 방법

# %% [markdown]
# ### Rolling FF3F beta

# %% [markdown]
# $ r_{i,t}^{e} = \beta_{i,t}^{\prime} f_{t} + \epsilon_{i,t}, \quad t = 1, 2, \dots, T. $
#
# for each stock at time t, use 60-month data to get beta

# %% [markdown]
# ### Time Varying Beta

# %%
group = list(np.unique(data.variable))
# data[data.variable==group[0]] # restrict the data within a specific group

# %%
for g in range(len(group)):
    a = data[data.variable==group[g]][['date', 'variable']]
    b = RollingOLS.from_formula('exret ~ mktrf + hml + smb', data=data[data.variable==group[g]], window=60).fit().params

    if g == 0:
        df = pd.concat([a, b], axis=1)
    else:
        df = pd.concat([df, pd.concat([a, b], axis=1)], axis=0)

# %%
df.columns = ['date', 'variable', 'alpha', 'beta_mkt', 'beta_hml', 'beta_smb']

# %%
ff_beta = pd.merge(data, df, on=['date', 'variable'], how='left')

# %%
ff_beta

# %% [markdown]
# ### Fama-Macbeth Regression

# %% [markdown]
# $$
#
# \begin{align*}
# r_{i,t}^{e} &= \beta_{i,t}^{\prime} \lambda_{t} + \alpha_{i,t}, \quad i = 1, 2, \dots, N \quad \text{for each } t. \\
# \\
# \hat{\lambda}_{FM} &= \frac{1}{T} \sum_{t=1}^{T} \hat{\lambda}_{t}, \quad \hat{\alpha}_{i,FM} = \frac{1}{T} \sum_{t=1}^{T} \hat{\alpha}_{i,t} \\
# \\
# \text{Var}( \hat{\lambda}_{FM} ) &= \frac{1}{T^2} \text{Var} \left( \sum_{t=1}^{T} \hat{\lambda}_{t} \right) = \frac{1}{T} \text{Var}( \hat{\lambda}_{t} ) = \frac{1}{T^2} \sum_{t=1}^{T} ( \hat{\lambda}_{t} - \hat{\lambda}_{FM} )^2 \\
# \\
# \text{Var}( \hat{\alpha}_{i,FM} ) &= \text{Var} \left( \frac{1}{T} \sum_{t=1}^{T} \hat{\alpha}_{i,t} \right) = \frac{1}{T} \text{Var}( \hat{\alpha}_{i,t} ) = \frac{1}{T^2} \sum_{t=1}^{T} ( \hat{\alpha}_{i,t} - \hat{\alpha}_{i,FM} )^2
# \end{align*}
#
# $$

# %% [markdown]
# ### Cross sectional regression for each t

# %%
ff_beta = ff_beta[~ff_beta.isna().any(axis=1)] # drop rows with NA values
time = np.unique(ff_beta.date)

# %%
for t in range(len(time)): # for each time t, run cross-sectional regression
    result = pd.DataFrame(smf.ols('exret ~ beta_mkt + beta_hml + beta_smb - 1', data=ff_beta[ff_beta.date==time[t]]).fit().params)
    result.columns = [time[t]]

    resid = pd.DataFrame(smf.ols(formula='exret ~ beta_mkt + beta_hml + beta_smb - 1', data=ff_beta[ff_beta.date==time[t]]).fit().resid)
    resid = pd.concat([ff_beta[ff_beta.date==time[t]][['variable', 'date']], resid], axis=1)

    if t == 0:
        cs_res = result
        alpha = resid
    else:
        cs_res = pd.concat([cs_res, result], axis=1)
        alpha = pd.concat([alpha, resid], axis=0)

# %%
cs_res = cs_res.T
cs_res

# %%
alpha.head()

# %% [markdown]
# ### FM coefficients

# %% [markdown]
# $$
#
# \hat{\lambda}_{FM} = \frac{1}{T} \sum_{t=1}^{T} \hat{\lambda}_{t}
#
# $$

# %%
## estimates

estimates = pd.DataFrame(cs_res.mean()) # Time-series average will be the resulting coefficient
estimates.columns = ['coefficients']
estimates * 12 # annualized

# %% [markdown]
# $$
#
# Var( \hat{\lambda}_{FM} ) = \frac{1}{T^2} Var \left( \sum_{t=1}^{T} \hat{\lambda}_{t} \right) = \frac{1}{T} Var( \hat{\lambda}_{t} ) = \frac{1}{T^2} \sum_{t=1}^{T} ( \hat{\lambda}_{t} - \hat{\lambda}_{FM} )^2
#
# $$

# %%
## standard errors 

variance = np.full(3, np.nan)

for i in range(3):
    variance[i] = (sum((cs_res.iloc[:, i] - cs_res.iloc[:, i].mean())**2) / (len(cs_res)**2)) ** 0.5

# %%
variance = pd.DataFrame(variance)
variance.index=['beta_mkt', 'beta_hml', 'beta_smb']

# %%
variance.columns = ['s.e']

# %%
result = pd.concat([estimates, variance], axis=1)
result['t' ] = result['coefficients'] / result['s.e']
result

# %% [markdown]
# ### Alpha

# %% [markdown]
# $$
#
# \hat{\alpha}_{i,FM} = \frac{1}{T} \sum_{t=1}^{T} \hat{\alpha}_{i,t}
#
# $$
#
# Check if alpha is collctively zero

# %%
alpha_fm = alpha.groupby('variable').mean()
alpha_fm = alpha_fm.reset_index()


# %%
alpha_fm.columns = ['variable', 'date', 'alpha_fm']

# %%
alpha.columns = ['variable', 'date', 'alpha']

# %%
variance = alpha.pivot_table(index='date', columns='variable', values='alpha')

# %%
variance = np.cov(np.asmatrix(variance.values).T)
variance.shape

# %%
ndates = len(alpha['date'].unique())
ndates

# %%
variance = variance / ndates

# %% [markdown]
# ### Joint Alpha Test

# %% [markdown]
# $$
#
# \hat{\alpha}_{i,FM}^{\prime} \cdot Var(\hat{\alpha}_{i,FM})^{-1} \hat{\alpha}_{i,FM} \sim \chi_{N-K}^2
#
# $$

# %%
al = np.asmatrix(alpha_fm['alpha_fm'].values)
al

# %%
chisq = al @ np.linalg.inv(variance) @ al.T

# %%
chisq

# %%
pval = 1 - stats.chi2(25 - 3).cdf(chisq)

# %%
pval

# %%
pval < 0.05

# %% [markdown]
# ## Method 2. linearmodels package

# %%
mulidx_ff_beta = ff_beta.set_index(['variable', 'date'], inplace=False)

# %%
mulidx_ff_beta = mulidx_ff_beta[['exret', 'beta_mkt', 'beta_hml', 'beta_smb']]

# %%
dependent = mulidx_ff_beta['exret']
exog = mulidx_ff_beta[['beta_mkt', 'beta_hml', 'beta_smb']]

# %%
lm_model = lm.panel.model.FamaMacBeth(dependent, exog)
lm_result = lm_model.from_formula('exret ~ beta_mkt + beta_hml + beta_smb - 1', data=mulidx_ff_beta).fit()


# %%
lm_result

# %% [markdown]
# Confirmed: two methods give the same results

# %% [markdown]
# ## Newey West standard errors

# %%
lm_model = lm.panel.model.FamaMacBeth(
    dependent, 
    exog,
    )
lm_result = lm_model.fit(
    cov_type='kernel',
    bandwidth=2,
    kernel='newey-west',
)


# %%
lm_result

# %%
