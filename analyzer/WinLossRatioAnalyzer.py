import backtrader as bt

class WinLossRatioAnalyzer(bt.Analyzer):
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.win_profits = []
        self.loss_profits = []
        self.trades = 0

    def notify_trade(self, trade):
        if trade.isclosed:
            pnl = trade.pnl
            self.trades += 1
            if pnl > 0:
                self.wins += 1
                self.win_profits.append(pnl)
            else:
                self.losses += 1
                self.loss_profits.append(pnl)

    def get_analysis(self):
        win_rate = (self.wins / self.trades) * 100 if self.trades else 0
        avg_win = sum(self.win_profits) / len(self.win_profits) if self.win_profits else 0
        avg_loss = sum(self.loss_profits) / len(self.loss_profits) if self.loss_profits else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        return {
            'total_trades': self.trades,
            'win_rate': win_rate,
            'wins': self.wins,
            'losses': self.losses,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio
        }
