import React, { useState, useEffect } from 'react';
import { Option, Portfolio } from './types/options';
import { calculatePortfolioMetrics } from './utils/optionsCalculations';
import { AddOptionForm } from './components/AddOptionForm';
import { OptionCard } from './components/OptionCard';
import { PortfolioSummary } from './components/PortfolioSummary';
import { Plus, BarChart3, List, Settings } from 'lucide-react';

function App() {
  const [options, setOptions] = useState<Option[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'options'>('overview');

  // Load options from localStorage on component mount
  useEffect(() => {
    const savedOptions = localStorage.getItem('options-tracker');
    if (savedOptions) {
      try {
        setOptions(JSON.parse(savedOptions));
      } catch (error) {
        console.error('Error loading saved options:', error);
      }
    }
  }, []);

  // Save options to localStorage whenever options change
  useEffect(() => {
    localStorage.setItem('options-tracker', JSON.stringify(options));
  }, [options]);

  const handleAddOption = (newOptionData: Omit<Option, 'id'>) => {
    const newOption: Option = {
      ...newOptionData,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9)
    };
    setOptions(prev => [...prev, newOption]);
  };

  const handleEditOption = (updatedOption: Option) => {
    setOptions(prev => prev.map(option => 
      option.id === updatedOption.id ? updatedOption : option
    ));
  };

  const handleDeleteOption = (id: string) => {
    if (window.confirm('Are you sure you want to delete this option?')) {
      setOptions(prev => prev.filter(option => option.id !== id));
    }
  };

  const handleUpdatePrice = (id: string, newPrice: number) => {
    setOptions(prev => prev.map(option => 
      option.id === id ? { ...option, currentPrice: newPrice } : option
    ));
  };

  // Calculate portfolio metrics
  const portfolio: Portfolio = {
    id: '1',
    name: 'My Options Portfolio',
    options,
    ...calculatePortfolioMetrics(options)
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'options', label: 'Options', icon: List }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Options Profit Tracker</h1>
            </div>
            <button
              onClick={() => setShowAddForm(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus size={16} />
              <span>Add Option</span>
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as 'overview' | 'options')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon size={16} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-3xl font-bold text-gray-900">Portfolio Overview</h2>
            </div>
            
            {options.length === 0 ? (
              <div className="text-center py-12">
                <div className="mx-auto h-12 w-12 text-gray-400">
                  <BarChart3 size={48} />
                </div>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No options yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by adding your first option position.
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="btn-primary"
                  >
                    <Plus size={16} className="mr-2" />
                    Add Option
                  </button>
                </div>
              </div>
            ) : (
              <PortfolioSummary portfolio={portfolio} />
            )}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-3xl font-bold text-gray-900">My Options</h2>
              <div className="text-sm text-gray-500">
                {options.length} option{options.length !== 1 ? 's' : ''}
              </div>
            </div>
            
            {options.length === 0 ? (
              <div className="text-center py-12">
                <div className="mx-auto h-12 w-12 text-gray-400">
                  <List size={48} />
                </div>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No options yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by adding your first option position.
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="btn-primary"
                  >
                    <Plus size={16} className="mr-2" />
                    Add Option
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {options.map((option) => (
                  <OptionCard
                    key={option.id}
                    option={option}
                    onEdit={handleEditOption}
                    onDelete={handleDeleteOption}
                    onUpdatePrice={handleUpdatePrice}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Add Option Form Modal */}
      {showAddForm && (
        <AddOptionForm
          onAddOption={handleAddOption}
          onClose={() => setShowAddForm(false)}
        />
      )}
    </div>
  );
}

export default App;