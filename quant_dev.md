> 大方向上可以分为alpha、beta两大流派
>
> alpha追求中性，无视市场变化，赚取波动价差，中高频，持有1天以上就算低频了
>
> beta更类似传统主观交易，更加有纪律

# 数据源

| --            | --        |
| ------------- | --------- |
| **free**      |           |
| yfinance      |           |
| alpha vantage | - [ ] asd |
| **charge**    |           |
| tradingview   |           |

- [ ] 支持A股 tushare 下载
  


# 策略

> 第一阶段以低频交易为主
>
> 1. 贴近主观交易：保留“选行业/找主线”的感觉；宏观经济认识；
>
> 2. 又可以用 Python / Pandas / 回测框架跑出历史数据来验证逻辑；
>
> 3. 把“拍脑袋”换成定量的因子系统，各类指标更加明确精准；
> 4. 增强交易纪律性，信号、仓位管理



* 对比估值？两只类似股票，出现估值缺口
* 多因子CTA
  * 复现研报-简单论文

## macky

| indicators           | buy & sell                                                   | perfomance | comment                                                      |
| -------------------- | ------------------------------------------------------------ | ---------- | ------------------------------------------------------------ |
| 20d highest / lowest | - when break, buy (next day open)<br />- close after 3 days  | -3.81%     | - blindly chase rising<br />- how to define the resist/support? |
|                      | - when break, wait n days, make sure it remain above the resist | -3.67%     |                                                              |

- [ ] macky

  - [ ] how to define resist & support?
    - [x] 20 days highest / lowest
    - [ ] pivot points
  - [ ] consider resist turn to support when break
  - [ ] indicators are too mechanical
    - [ ] increase trading frequency (30min, 1h)
    - [ ] deep-learning(parameterization)
  - [ ] take profit / stop loss
  - [ ] param adjust
    - [ ] close price

  - [ ] recognize left side / right side, depend on news

- [ ] KDJ，勾到大负值

- [ ] 选股





# 回测

- [ ] calc beta
- [ ] minute-level backtest



# 学习资源

| --     | --                                                           |
| ------ | ------------------------------------------------------------ |
| 李不白 | [bilibili](https://space.bilibili.com/3546791769279104?spm_id_from=333.1387.follow.user_card.click) |
|        | [red](https://www.xiaohongshu.com/user/profile/5f5eeab900000000010047bc?xsec_token=ABuufNWq0rQRznfAUzNjZ6-5ZJYu-DC1GR3Dyn8F34naM%3D&xsec_source=pc_search) |
| 知乎   |                                                              |

