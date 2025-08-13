# Options Profit Tracker

A modern, responsive web application for tracking options trades and calculating profit/loss metrics. Built with React, TypeScript, and Tailwind CSS.

## Features

### 📊 Portfolio Overview
- **Real-time P&L tracking** - Monitor unrealized gains and losses
- **Portfolio allocation charts** - Visual representation of your options distribution
- **Performance metrics** - Total value, cost, and percentage returns
- **Quick statistics** - Count of calls vs puts, average costs, and more

### 📈 Options Management
- **Add new options** - Easy form to input trade details
- **Edit existing positions** - Update prices and quantities
- **Delete positions** - Remove closed or unwanted trades
- **Real-time price updates** - Inline editing of current option prices

### 🎯 Advanced Calculations
- **Break-even analysis** - Know exactly when your options become profitable
- **Days to expiration** - Track time decay with color-coded warnings
- **P&L percentages** - Both absolute and relative performance metrics
- **Portfolio aggregation** - Combined metrics across all positions

### 💾 Data Persistence
- **Local storage** - Your data persists between browser sessions
- **No external dependencies** - Works completely offline
- **Secure** - All data stays on your device

## Getting Started

### Prerequisites
- Node.js (version 14 or higher)
- npm or yarn package manager

### Installation

1. **Clone or download** the project files
2. **Navigate** to the project directory:
   ```bash
   cd options-profit-tracker
   ```

3. **Install dependencies**:
   ```bash
   npm install
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

5. **Open your browser** and navigate to `http://localhost:3000`

### Building for Production

To create a production build:

```bash
npm run build
```

The built files will be in the `build/` directory.

## Usage

### Adding Options

1. Click the **"Add Option"** button in the header
2. Fill out the form with your trade details:
   - **Symbol** (e.g., AAPL, TSLA)
   - **Option Type** (Call or Put)
   - **Strike Price**
   - **Expiration Date**
   - **Current Market Price**
   - **Quantity** (number of contracts)
   - **Entry Price** (what you paid)
   - **Entry Date**
   - **Notes** (optional)

3. Click **"Add Option"** to save

### Managing Positions

- **View details**: Click the expand arrow on any option card
- **Update prices**: Click the edit icon to modify current market prices
- **Delete positions**: Click the trash icon to remove closed trades
- **Track performance**: Monitor P&L in real-time as you update prices

### Portfolio Analysis

- **Overview tab**: See portfolio-wide metrics and charts
- **Options tab**: Detailed view of individual positions
- **Charts**: Visual representation of allocation and performance

## Technical Details

### Architecture
- **Frontend**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom component classes
- **Charts**: Recharts library for data visualization
- **Icons**: Lucide React for consistent iconography
- **State Management**: React hooks with localStorage persistence

### Key Components
- `App.tsx` - Main application component
- `AddOptionForm.tsx` - Modal form for adding options
- `OptionCard.tsx` - Individual option display and management
- `PortfolioSummary.tsx` - Portfolio overview and charts
- `types/options.ts` - TypeScript interfaces
- `utils/optionsCalculations.ts` - Financial calculation utilities

### Data Structure

```typescript
interface Option {
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
```

## Customization

### Styling
The application uses Tailwind CSS with custom color schemes. You can modify:
- `tailwind.config.js` - Color palette and theme extensions
- `src/index.css` - Custom component classes and global styles

### Calculations
Financial calculations are in `src/utils/optionsCalculations.ts`. You can:
- Modify P&L calculation methods
- Add new financial metrics
- Customize formatting functions

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Disclaimer

This application is for educational and personal use only. It is not financial advice and should not be used as the sole basis for investment decisions. Always consult with a qualified financial advisor before making investment decisions.

## Support

If you encounter any issues or have questions:
1. Check the browser console for error messages
2. Ensure all dependencies are properly installed
3. Verify your Node.js version is compatible
4. Clear browser cache and localStorage if needed

---

**Happy Trading! 📈**
