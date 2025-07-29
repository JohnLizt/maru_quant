# Data Source

| source             | cost (month) | earliest  | comment                               |
| ------------------ | ------------ | --------- | ------------------------------------- |
| yfinance           | free         | no data   |                                       |
| alpha vantage      | free         | 2020-     | has 9pm data, maybe calculated result |
| tradingview        | 14$          | 2023-     | **realtime**<br />download fast       |
| **tickstory_lite** | **free**     | **2003-** | **unbelievable slow**                 |
| tick data manager  |              |           |                                       |
| MT4                |              |           |                                       |



# CTA

> 量化大方向上可以分为alpha、beta两大流派
>
> alpha追求中性，无视市场变化，赚取波动价差，中高频，持有1天以上就算低频了
>
> beta更类似传统主观交易，受行情影响、波动都很大
>
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

- [ ] 黄金品类研究
  - [ ] 金价影响因素
  - [ ] 美元影响因素
- [ ] CTA策略研究
  - [ ] 突破策略
  - [ ] 多因子策略框架
  - [ ] 事件驱动策略框架



## **Trend Tracking**

> 适用于上涨/下跌行情，震荡市容易出事

### SMA

> 本质上是趋势追踪（追涨杀跌），适用于上涨/下跌行情

### Breakout （施工中）

> 压力位/支撑位的本质：**集体意识**;  人们对于区域顶部和底部的记忆是最深刻的，形成了集体的自证预言。参考我自己买日元的经历，第一次碰到4.8没有买，看到涨价到5以上，内心非常后悔，下次价格一触及4.8就会立刻买入。因此，假设在无干扰环境下价格会在一个区间内波动，类似三角函数；既然能突破区间，说明有外部力量影响，这种大的力量可能会形成趋势，从而有跟随获利的可能性。
>
> breakout策略核心思路是抓住成功突破后的一波行情，属于偏主观的趋势策略，**震荡市会非常难受**，上涨/下跌行情表现较好。操作思路上：信号要卡严一点，过滤掉大量的假突破、弱信号；止盈止损很重要，需要好好设置
>
> 集体意识的概念，主要用于收割人工玩家，但是黄金市场的**量化玩家似乎占比60%以上**，可能需要重新考虑更优的策略

- [ ] **indicator**
  - [x] ~~extreme~~
  - [x] pivot high/low
    - [x] ~~smoothed：resistance zone~~
    - [x] support represent (broken resist automatically become support)
    - [x] ~~expand resist queue~~
  - [ ] AlgoAlpha: resist and breakout
  - [ ] 布林带,  Keltner channel， Donchain channel， 海龟交易法则
- [ ] **breakout signal**
  - [x] ~~candle shape~~
    - [x] ~~CSI~~
  - [x] SMA crossover resist
    - [x] EMA
  - [x] ~~multi-break~~
- [ ] **trend filter**
  - [ ] ATR filter
  - [ ] avoid big volatility (time period, news)  https://www.forexfactory.com/
  - [ ] timezone filter
- [ ] **trade management**
  - [x] take profit / stop loss
    - [x] ATR
  - [ ] <u>parallel position</u>
  - [ ] adaptive sizer
    - [ ] resist / support intensity
    - [ ] breakout intensity
  - [ ] ~~dynamic spread~~
    - [ ] ~~Tick Data Suite~~
- [ ] **live trading**
- [ ] **optimization**
  - [x] ~~higher frequency (10min?)~~
  - [x] grid search optimizer
  - [x] walk forward analysis
    - [ ] refine WFE
  - [ ] ML / DL



#### ATR stop loss

> * ATR
>
> ATR (usually around 5) * k (2 by default) ≈ 10
>
> for XAUUSD 30min, k usually around 6 ~ 10
>
> * ATR period (default 14)



## Multi Factor



## Event-Driven

### LLM-news

* 早鸟策略：新闻发出时快速买入
* 买预期卖事实：在“靴子落地”时，提前布局的主力获利了结，往往有预期反方向的动能



# **Strategy Performance** 

> **data**: past 5 years
>
> **window**: 1 year train, half year test
>
> **account**: 500 cash, 0.01 lot (**return** is related to initial cash, here we use very conservative value)
>
> final summarize: use **<u>Exponent Moving Avg</u>** for better reflect recent performance
>
> WFE这个指标目前不是很好用，看起来优化参数组合给的越多，这个值越大代表过拟合，或许需要固定参数跑WFA

| strategy       | sharpe | max_dd  | return | win_rate | PL_ratio | WFE           | comment  |
| -------------- | ------ | ------- | ------ | -------- | -------- | ------------- | -------- |
| **SMA**        | 0.8954 | 27.1486 | 0.2061 | 26.7742  | 3.0138   | 0.6959∓2.2593 | baseline |
| PivotBreakout | 1.7367 | 14.9393 | 0.2874 | 56.1124  | 1.2534   | 1.4636∓1.4898 | nice     |
|                |        |         |        |          |          |               |          |





# BackTesting

* **策略检验流程**

> 1. 人工分析：短周期，验证基本逻辑，初步估计参数范围（可以用optimizer调参）
>    - 长周期回测：筛选掉明显弱的策略，短周期表现好可以跳过
> 2. WFA优化：多周期调参，投票法选择参数组合
>    * 配合不强的参数分开调，最好一次精调一个参数，距离 like [0.01, 0.1, 0.3, 0.5, 1]  
> 3. WFA横评：固定参数，检验策略效果



## WFA

> Walk Forward Analysis 滑动窗口多周期优化 + 验证，优点：
>
> 1. 综合检验策略性能（未来预测能力、跨市场周期鲁棒性）
> 2. WFE：检验策略是否过拟合
> 3. 有一定的参数优化能力，实盘可直接采用步进优化
>
> - 窗口长度如何设置
>
> 窗口过短，夏普率计算不可信，因此测试集至少要半年以上（6000条）
>
> 窗口过长，会出现测试集集中在后面年份，市场差距太大
>
> - 参数不续训：倾向验证策略本身而不是参数
>
> 
>
> ## **WFE想验证的核心问题**
>
> ### A. **模型/参数是否具有可迁移性**
>
> - 训练期参数/模型在未来（测试期）是否依然有效。
> - 换句话说，策略是否过拟合历史数据，还是能适应未来市场变化。
>
> ### B. **样本外表现与样本内的关系**
>
> - 理想状态：样本外（test）表现与样本内（train）表现接近，WFE接近1。
> - 如果样本外显著逊色于样本内，WFE远小于1（甚至为负），说明策略过拟合或不稳定。
> - 如果样本外反而优于样本内，WFE大于1，可能是市场变化带来的偶然结果，也需警惕。
>
> ### C. **策略的鲁棒性与稳定性**
>
> - 多窗口滚动下，WFE的分布反映了策略在不同市场阶段、参数组合下的稳定性。
> - WFE均值高且分布集中，说明策略稳健；极端波动说明策略对市场变化敏感，风险大。



# Live Trading





# 学习资源

| --           | --                                                           |
| ------------ | ------------------------------------------------------------ |
| 李不白       | [bilibili](https://space.bilibili.com/3546791769279104?spm_id_from=333.1387.follow.user_card.click) |
|              | [red](https://www.xiaohongshu.com/user/profile/5f5eeab900000000010047bc?xsec_token=ABuufNWq0rQRznfAUzNjZ6-5ZJYu-DC1GR3Dyn8F34naM%3D&xsec_source=pc_search) |
| 黄金外汇MT4  | https://space.bilibili.com/1324136602?spm_id_from=333.788.upinfo.head.click |
| 基本指标知识 | https://www.bilibili.com/video/BV12L4y1L7TA?spm_id_from=333.788.videopod.sections&vd_source=feacdd607007d02479769d9056af2634 |
| 知乎         |                                                              |
| MQL5         |                                                              |

## candles theory

| --           | --            |
| ------------ | ------------- |
| candle wick  | means strong? |
| fill the gap |               |

## commodity 基础知识

> 看成加杠杆的股票就行，不过加个杠杆
>
> 关于杠杆：简单来说，同样仓位下，杠杆越大越好



# Dev

```python
# debug
bt.num2date(self.datas[0].datetime[0]).strftime('%Y-%m-%d %H:%M:%S') == '2020-06-09 12:00:00'
```



| strategy   | info                                                         | review                                                       |
| ---------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **resist** |                                                              | **accuracy & recall**                                        |
| v1.00      | 1. use extreme value as resist / support 2. breakout -> buy / breakdown -> sell  3. close after 3 t | 1. chase rising                                              |
| v1.01      | 1. break -> observe -> buy + sell 2. CSI: candle strength index 3. add take profit / stop loss | 1.resist definition not good                                 |
| v1.02      | 1. pivot: slide windows + monostack 2. simple breakout strategy | 1.too decrete                                                |
| v1.0.3     | 1. sma simple breakout strategy 2. grid search optimizer 3. train-test split 4. size management | 1. latency;  2. not good at big volatility 3. too many fake breakout |
| v1.0.4     | 1. compare sma, ema, wma 2. commission info (margin, leverage...) 3. bracket orders | 1.fake breakout 2.avoid fierce volatility 3.take profit/ stop loss too fierce, not smooth 4.trend filter |
| v1.0.5     | 1. WFA framework  2. logger 3. baselines                     | 1.WFE not very stable                                        |
| v1.0.6     | 1. living trading via MT5                                    |                                                              |
| v1.0.7     | 1. dynamic take profit / stop loss                           |                                                              |

