import React, { useState } from 'react';
import { Option, OptionProfitLoss } from '../types/options';
import { calculateOptionProfitLoss, formatCurrency, formatPercentage, calculateDaysToExpiration } from '../utils/optionsCalculations';
import { Edit2, Trash2, ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react';

interface OptionCardProps {
  option: Option;
  onEdit: (option: Option) => void;
  onDelete: (id: string) => void;
  onUpdatePrice: (id: string, newPrice: number) => void;
}

export const OptionCard: React.FC<OptionCardProps> = ({
  option,
  onEdit,
  onDelete,
  onUpdatePrice
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditingPrice, setIsEditingPrice] = useState(false);
  const [newPrice, setNewPrice] = useState(option.currentPrice.toString());

  // Mock current market price (in real app, this would come from API)
  const currentMarketPrice = option.currentPrice;
  const profitLoss = calculateOptionProfitLoss(option, currentMarketPrice);
  const daysToExpiration = calculateDaysToExpiration(option.expirationDate);

  const handlePriceUpdate = () => {
    const price = parseFloat(newPrice);
    if (!isNaN(price) && price >= 0) {
      onUpdatePrice(option.id, price);
      setIsEditingPrice(false);
    }
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-success-600';
    if (pnl < 0) return 'text-danger-600';
    return 'text-gray-600';
  };

  const getExpirationColor = (days: number) => {
    if (days <= 7) return 'text-danger-600';
    if (days <= 30) return 'text-yellow-600';
    return 'text-gray-600';
  };

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            option.type === 'call' 
              ? 'bg-blue-100 text-blue-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {option.type.toUpperCase()}
          </div>
          <h3 className="text-lg font-semibold text-gray-900">{option.symbol}</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsEditingPrice(!isEditingPrice)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Edit price"
          >
            <Edit2 size={16} />
          </button>
          <button
            onClick={() => onDelete(option.id)}
            className="p-1 text-gray-400 hover:text-danger-600 transition-colors"
            title="Delete option"
          >
            <Trash2 size={16} />
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-500">Strike Price</p>
          <p className="font-medium">{formatCurrency(option.strikePrice)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Current Price</p>
          <div className="flex items-center space-x-2">
            {isEditingPrice ? (
              <>
                <input
                  type="number"
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  className="input-field w-20 h-8 text-sm"
                  step="0.01"
                  min="0"
                />
                <button
                  onClick={handlePriceUpdate}
                  className="text-xs bg-primary-600 text-white px-2 py-1 rounded"
                >
                  ✓
                </button>
              </>
            ) : (
              <p className="font-medium">{formatCurrency(option.currentPrice)}</p>
            )}
          </div>
        </div>
        <div>
          <p className="text-sm text-gray-500">Quantity</p>
          <p className="font-medium">{option.quantity}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Expires In</p>
          <p className={`font-medium ${getExpirationColor(daysToExpiration)}`}>
            {daysToExpiration} days
          </p>
        </div>
      </div>

      <div className="border-t pt-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">Unrealized P&L</span>
          <div className="flex items-center space-x-1">
            {profitLoss.unrealizedPnL > 0 ? (
              <TrendingUp size={16} className="text-success-600" />
            ) : profitLoss.unrealizedPnL < 0 ? (
              <TrendingDown size={16} className="text-danger-600" />
            ) : null}
            <span className={`font-semibold ${getPnLColor(profitLoss.unrealizedPnL)}`}>
              {formatCurrency(profitLoss.unrealizedPnL)}
            </span>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">P&L %</span>
          <span className={`font-medium ${getPnLColor(profitLoss.unrealizedPnLPercent)}`}>
            {formatPercentage(profitLoss.unrealizedPnLPercent)}
          </span>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t pt-4 mt-4 space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Entry Price</p>
              <p className="font-medium">{formatCurrency(option.entryPrice)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Entry Date</p>
              <p className="font-medium">{new Date(option.entryDate).toLocaleDateString()}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Break Even</p>
              <p className="font-medium">{formatCurrency(profitLoss.breakEvenPrice)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Cost</p>
              <p className="font-medium">{formatCurrency(profitLoss.totalCost)}</p>
            </div>
          </div>

          {option.notes && (
            <div>
              <p className="text-sm text-gray-500">Notes</p>
              <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded">{option.notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};