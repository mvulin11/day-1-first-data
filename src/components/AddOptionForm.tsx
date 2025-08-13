import React, { useState } from 'react';
import { Option } from '../types/options';
import { Plus, X } from 'lucide-react';

interface AddOptionFormProps {
  onAddOption: (option: Omit<Option, 'id'>) => void;
  onClose: () => void;
}

export const AddOptionForm: React.FC<AddOptionFormProps> = ({ onAddOption, onClose }) => {
  const [formData, setFormData] = useState({
    symbol: '',
    type: 'call' as 'call' | 'put',
    strikePrice: '',
    expirationDate: '',
    currentPrice: '',
    quantity: '',
    entryPrice: '',
    entryDate: new Date().toISOString().split('T')[0],
    notes: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const newOption: Omit<Option, 'id'> = {
      ...formData,
      strikePrice: parseFloat(formData.strikePrice),
      currentPrice: parseFloat(formData.currentPrice),
      quantity: parseInt(formData.quantity),
      entryPrice: parseFloat(formData.entryPrice)
    };

    onAddOption(newOption);
    onClose();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Add New Option</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Symbol
              </label>
              <input
                type="text"
                name="symbol"
                value={formData.symbol}
                onChange={handleChange}
                className="input-field"
                placeholder="AAPL"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                name="type"
                value={formData.type}
                onChange={handleChange}
                className="input-field"
              >
                <option value="call">Call</option>
                <option value="put">Put</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Strike Price
              </label>
              <input
                type="number"
                name="strikePrice"
                value={formData.strikePrice}
                onChange={handleChange}
                className="input-field"
                step="0.01"
                min="0"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expiration Date
              </label>
              <input
                type="date"
                name="expirationDate"
                value={formData.expirationDate}
                onChange={handleChange}
                className="input-field"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Price
              </label>
              <input
                type="number"
                name="currentPrice"
                value={formData.currentPrice}
                onChange={handleChange}
                className="input-field"
                step="0.01"
                min="0"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Quantity
              </label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                className="input-field"
                min="1"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Entry Price
              </label>
              <input
                type="number"
                name="entryPrice"
                value={formData.entryPrice}
                onChange={handleChange}
                className="input-field"
                step="0.01"
                min="0"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Entry Date
              </label>
              <input
                type="date"
                name="entryDate"
                value={formData.entryDate}
                onChange={handleChange}
                className="input-field"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              className="input-field"
              rows={3}
              placeholder="Optional notes about this trade..."
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1 flex items-center justify-center"
            >
              <Plus size={16} className="mr-2" />
              Add Option
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};