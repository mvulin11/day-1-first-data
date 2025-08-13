export interface Option {
  id: string;
  symbol: string;
  type: 'call' | 'put';
  strikePrice: number;
  expirationDate: string;
  currentPrice: number;
  quantity: number;
  entryPrice: number;
  entryDate: string;
  notes?: string;
}

export interface OptionProfitLoss {
  option: Option;
  currentValue: number;
  totalCost: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  breakEvenPrice: number;
}

export interface Portfolio {
  id: string;
  name: string;
  options: Option[];
  totalValue: number;
  totalCost: number;
  totalPnL: number;
  totalPnLPercent: number;
}

export interface MarketData {
  symbol: string;
  currentPrice: number;
  change: number;
  changePercent: number;
  volume: number;
}