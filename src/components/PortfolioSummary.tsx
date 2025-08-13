import React from 'react';
import { Portfolio } from '../types/options';
import { formatCurrency, formatPercentage } from '../utils/optionsCalculations';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Calendar } from 'lucide-react';

interface PortfolioSummaryProps {
  portfolio: Portfolio;
}

export const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({ portfolio }) => {
  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-success-600';
    if (pnl < 0) return 'text-danger-600';
    return 'text-gray-600';
  };

  const getPnLIcon = (pnl: number) => {
    if (pnl > 0) return <TrendingUp size={20} className="text-success-600" />;
    if (pnl < 0) return <TrendingDown size={20} className="text-danger-600" />;
    return null;
  };

  // Prepare data for pie chart
  const pieData = portfolio.options.map(option => ({
    name: option.symbol,
    value: option.currentPrice * option.quantity * 100,
    color: option.type === 'call' ? '#3b82f6' : '#ef4444'
  }));

  // Calculate options by type
  const callsCount = portfolio.options.filter(o => o.type === 'call').length;
  const putsCount = portfolio.options.filter(o => o.type === 'put').length;

  return (
    <div className="space-y-6">
      {/* Portfolio Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Value</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(portfolio.totalValue)}
              </p>
            </div>
            <DollarSign size={24} className="text-primary-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Cost</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(portfolio.totalCost)}
              </p>
            </div>
            <DollarSign size={24} className="text-gray-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Unrealized P&L</p>
              <div className="flex items-center space-x-2">
                {getPnLIcon(portfolio.totalPnL)}
                <p className={`text-2xl font-bold ${getPnLColor(portfolio.totalPnL)}`}>
                  {formatCurrency(portfolio.totalPnL)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">P&L %</p>
              <p className={`text-2xl font-bold ${getPnLColor(portfolio.totalPnLPercent)}`}>
                {formatPercentage(portfolio.totalPnLPercent)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts and Additional Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Allocation Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Allocation</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), 'Value']}
                  labelFormatter={(label) => `${label} Options`}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-6 mt-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Calls ({callsCount})</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Puts ({putsCount})</span>
            </div>
          </div>
        </div>

        {/* Portfolio Statistics */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Statistics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Total Options</span>
              <span className="font-medium">{portfolio.options.length}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Call Options</span>
              <span className="font-medium text-blue-600">{callsCount}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Put Options</span>
              <span className="font-medium text-red-600">{putsCount}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Average Cost</span>
              <span className="font-medium">
                {portfolio.options.length > 0 
                  ? formatCurrency(portfolio.totalCost / portfolio.options.length)
                  : '$0.00'
                }
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Average Value</span>
              <span className="font-medium">
                {portfolio.options.length > 0 
                  ? formatCurrency(portfolio.totalValue / portfolio.options.length)
                  : '$0.00'
                }
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};