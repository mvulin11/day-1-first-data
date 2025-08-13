import { Option, OptionProfitLoss } from '../types/options';

export const calculateOptionProfitLoss = (option: Option, currentMarketPrice: number): OptionProfitLoss => {
  const currentValue = option.currentPrice * option.quantity * 100; // Options are typically 100 shares
  const totalCost = option.entryPrice * option.quantity * 100;
  const unrealizedPnL = currentValue - totalCost;
  const unrealizedPnLPercent = totalCost !== 0 ? (unrealizedPnL / totalCost) * 100 : 0;
  
  // Calculate break-even price
  let breakEvenPrice = option.strikePrice;
  if (option.type === 'call') {
    breakEvenPrice = option.strikePrice + option.entryPrice;
  } else {
    breakEvenPrice = option.strikePrice - option.entryPrice;
  }

  return {
    option,
    currentValue,
    totalCost,
    unrealizedPnL,
    unrealizedPnLPercent,
    breakEvenPrice
  };
};

export const calculatePortfolioMetrics = (options: Option[]): {
  totalValue: number;
  totalCost: number;
  totalPnL: number;
  totalPnLPercent: number;
} => {
  const totalValue = options.reduce((sum, option) => 
    sum + (option.currentPrice * option.quantity * 100), 0);
  
  const totalCost = options.reduce((sum, option) => 
    sum + (option.entryPrice * option.quantity * 100), 0);
  
  const totalPnL = totalValue - totalCost;
  const totalPnLPercent = totalCost !== 0 ? (totalPnL / totalCost) * 100 : 0;

  return {
    totalValue,
    totalCost,
    totalPnL,
    totalPnLPercent
  };
};

export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

export const formatPercentage = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};

export const calculateDaysToExpiration = (expirationDate: string): number => {
  const today = new Date();
  const expiration = new Date(expirationDate);
  const diffTime = expiration.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return Math.max(0, diffDays);
};