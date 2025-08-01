import backtrader as bt

class WinLossRatioAnalyzer(bt.Analyzer):
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.win_profits = []
        self.loss_profits = []
        self.win_profit_rates = []
        self.loss_profit_rates = []
        self.trades = 0

    def notify_trade(self, trade):
        if trade.isclosed:
            pnl = trade.pnl
            # entry_price = trade.price
            # profit_rate = (pnl / entry_price) * 100  # 利润率百分比算不对？

            self.trades += 1
            if pnl > 0:
                self.wins += 1
                self.win_profits.append(pnl)
                # self.win_profit_rates.append(profit_rate)
            else:
                self.losses += 1
                self.loss_profits.append(pnl)
                # self.loss_profit_rates.append(profit_rate)

    def get_analysis(self):
        win_rate = (self.wins / self.trades) * 100 if self.trades else 0
        avg_win = sum(self.win_profits) / len(self.win_profits) if self.win_profits else 0
        avg_loss = sum(self.loss_profits) / len(self.loss_profits) if self.loss_profits else 0
        # avg_win_rate = sum(self.win_profit_rates) / len(self.win_profit_rates) if self.win_profit_rates else 0
        # avg_loss_rate = sum(self.loss_profit_rates) / len(self.loss_profit_rates) if self.loss_profit_rates else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        return {
            'total_trades': self.trades,
            'win_rate': win_rate,
            'wins': self.wins,
            'losses': self.losses,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            # 'avg_win_rate': avg_win_rate,
            # 'avg_loss_rate': avg_loss_rate,
            'P/L_ratio': profit_loss_ratio
        }
