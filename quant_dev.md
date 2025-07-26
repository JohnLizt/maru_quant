> 量化大方向上可以分为alpha、beta两大流派
>
> alpha追求中性，无视市场变化，赚取波动价差，中高频，持有1天以上就算低频了
>
> beta更类似传统主观交易，只是纪律性好

# 数据源

| --            | --        |
| ------------- | --------- |
| **free**      |           |
| yfinance      |           |
| alpha vantage | - [ ] asd |
| **charge**    |           |
| tradingview   |           |




# CTA strategy

> 1. **趋势跟踪（Trend Following）**
>    - 代表：SMA/EMA突破、Donchian通道、Turtle策略、ADX趋势跟随等
>    - 逻辑：价格突破某一均值或区间后顺势买入/卖出，长期持有趋势单
> 2. **均值回归（Mean Reversion）**
>    - 代表：布林带回归、Keltner通道、价差套利、振荡区间策略
>    - 逻辑：价格偏离均值后，预期其回归历史均值附近
> 3. **套利策略（Arbitrage）**
>    - 代表：跨期套利（Calendar Spread）、跨品种套利、统计套利（Pairs Trading）
>    - 逻辑：利用相关性、价差等市场无效性进行低风险套利
> 4. **动量策略（Momentum）**
>    - 代表：横截面动量（多品种间强者恒强）、时间序列动量（单品种顺势）
>    - 逻辑：近期涨得多的品种继续买入，跌得多的继续卖出
> 5. **反转策略（Reversal）**
>    - 代表：超买超卖反转（如RSI、CCI）、极端事件反转
>    - 逻辑：短期内涨跌过度，预期价格出现反转
> 6. **突破策略（Breakout）**
>    - 代表：区间突破、价格新高新低突破
>    - 逻辑：价格突破一段时间内高点/低点后追随
> 7. **波动率策略（Volatility）**
>    - 代表：基于波动率的波段交易、波动率扩张收缩策略
>    - 逻辑：利用波动率变化进行入场、出场或仓位调整
> 8. **资金管理与组合优化**
>    - 代表：多品种马丁格尔、凯利公式、动态止损止盈等



## **trend following**

> 适用于上涨/下跌行情，震荡市容易出事

### SMA

> 本质上是趋势追踪（追涨杀跌），适用于上涨/下跌行情



## event-driven

### LLM-news

* 早鸟策略：新闻发出时快速买入
* 买预期卖事实：在“靴子落地”时，提前布局的主力获利了结，往往有预期反方向的动能



## breakout ⭐

> 压力位/支撑位的本质：**群体心理学**;  人们对于区域顶部和底部的记忆是最深刻的，形成了集体的自证预言。
>
> 参考我自己买日元的经历，第一次碰到4.8没有买，看到涨价到5以上，内心非常后悔，下次价格一触及4.8就会立刻买入。
>
> breakout策略核心思路是抓住成功突破后的一波行情，感觉上偏主观，信号要卡严一点，过滤掉大量的假突破、弱信号，后续持仓可以放宽
>
> **震荡市会非常难受**，上涨/下跌行情表现较好

- [x] indicator: how to define resist & support?

  - [x] extreme value
  - [x] pivot high/low
  - [ ] bilibili

- [ ] breakout signal

  - [x] candle shape：CSI

  - [x] SMA crossover resist

    - [ ] EMA

  - [ ] multi-scale

  - [ ] CISD? wick must be filled, 80%

    > https://www.youtube.com/watch?v=EvG8vRTgRbU&t=3s
    >
    > https://www.bilibili.com/video/BV1D9GLzyEJF/?spm_id_from=333.1007.tianma.1-2-2.click&vd_source=feacdd607007d02479769d9056af2634

  - [ ] consider resist turn to support when break

  - [ ] resist / support intensity

- [ ] trade management

  - [x] take profit / stop loss
    - [ ] ATR dynamic param
  - [x] profit calc should multi leverage

- [ ] trend tracking

  - [ ] recognize left side / right side (via news or sth)

- [ ] optimization
  - [ ] higher frequency (10min?)
  - [ ] dynamic param (eg. ATR)
  - [x] grid search optimizer
  - [ ] ML / DL



| strategy   | info                                                         | test (uptrend) |         |            | review                                                       |
| ---------- | ------------------------------------------------------------ | -------------- | ------- | ---------- | ------------------------------------------------------------ |
| **resist** |                                                              | **WR**         | **P/L** | **profit** | **accuracy & recall**                                        |
| v1.00      | 1. use extreme value as resist / support<br />2. breakout -> buy / breakdown -> sell <br />3. close after 3 t | -              | -       | -3.81%     | 1. chase rising                                              |
| v1.01      | 1. break -> observe -> buy + sell<br />2. CSI: candle strength index<br />3. add take profit / stop loss | 33.33%         | 1.7     | -0.43%     | 1.resist definition not good                                 |
| v1.02      | 1. pivot: slide windows + monostack<br />2. simple breakout strategy | 47%            | 1.3     | 0.05%      | 1.too decrete                                                |
| v1.0.3     | 1. sma simple breakout strategy<br />2. grid search optimizer<br />3. train-test split<br />4. size management | 45%            | 1.8     | 5.6%       | 1. latency; <br />2. not good at big volatility<br />3. too many fake breakout |
| v1.0.4     | 1. compare sma, ema, wma, kama...                            |                |         |            | 1.fake breakout                                              |
|            |                                                              |                |         |            |                                                              |
|            | short order                                                  |                |         |            |                                                              |
|            | avoid volatility: news + ATR<br />                           |                |         |            |                                                              |
|            | integrate news:<br /> https://www.forexfactory.com/<br />    |                |         |            |                                                              |



### candles theory

| --           | --            |
| ------------ | ------------- |
| candle wick  | means strong? |
| fill the gap |               |



## multi factor



# live trading





# 学习资源

| --     | --                                                           |
| ------ | ------------------------------------------------------------ |
| 李不白 | [bilibili](https://space.bilibili.com/3546791769279104?spm_id_from=333.1387.follow.user_card.click) |
|        | [red](https://www.xiaohongshu.com/user/profile/5f5eeab900000000010047bc?xsec_token=ABuufNWq0rQRznfAUzNjZ6-5ZJYu-DC1GR3Dyn8F34naM%3D&xsec_source=pc_search) |
| 知乎   |                                                              |

