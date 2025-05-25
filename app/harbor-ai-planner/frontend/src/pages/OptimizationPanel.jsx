import React, { useState } from 'react';

// Ikoner
const ArrowUp = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="19" x2="12" y2="5"></line>
    <polyline points="5 12 12 5 19 12"></polyline>
  </svg>
);

const ArrowDown = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <polyline points="19 12 12 19 5 12"></polyline>
  </svg>
);

const BarChart = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="20" x2="12" y2="10"></line>
    <line x1="18" y1="20" x2="18" y2="4"></line>
    <line x1="6" y1="20" x2="6" y2="16"></line>
  </svg>
);

const DollarSign = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="1" x2="12" y2="23"></line>
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
  </svg>
);

const Calendar = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
    <line x1="16" y1="2" x2="16" y2="6"></line>
    <line x1="8" y1="2" x2="8" y2="6"></line>
    <line x1="3" y1="10" x2="21" y2="10"></line>
  </svg>
);

const Info = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="16" x2="12" y2="12"></line>
    <line x1="12" y1="8" x2="12.01" y2="8"></line>
  </svg>
);

const Download = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="7 10 12 15 17 10"></polyline>
    <line x1="12" y1="15" x2="12" y2="3"></line>
  </svg>
);

function Optimization() {
  const [selectedTimeframe, setSelectedTimeframe] = useState('month');
  const [selectedDock, setSelectedDock] = useState('all');
  
  // Exempelvärden för visualisering
  const performanceData = {
    occupancyRate: 72,
    occupancyTrend: '+5%',
    revenueUtilization: 68,
    revenueTrend: '+8%',
    customerSatisfaction: 85,
    satisfactionTrend: '+3%',
    maintenanceEfficiency: 92,
    maintenanceTrend: '+10%'
  };
  
  // Beläggning per månad för olika platstyper
  const occupancyByTypeData = [
    { month: 'Jan', small: 45, medium: 55, large: 70, xlarge: 65 },
    { month: 'Feb', small: 48, medium: 58, large: 68, xlarge: 70 },
    { month: 'Mar', small: 52, medium: 62, large: 72, xlarge: 75 },
    { month: 'Apr', small: 65, medium: 75, large: 85, xlarge: 80 },
    { month: 'Maj', small: 80, medium: 85, large: 95, xlarge: 100 },
    { month: 'Jun', small: 95, medium: 98, large: 100, xlarge: 100 },
    { month: 'Jul', small: 100, medium: 100, large: 100, xlarge: 100 },
    { month: 'Aug', small: 90, medium: 95, large: 98, xlarge: 100 },
    { month: 'Sep', small: 75, medium: 80, large: 85, xlarge: 90 },
    { month: 'Okt', small: 60, medium: 65, large: 70, xlarge: 75 },
    { month: 'Nov', small: 50, medium: 60, large: 65, xlarge: 70 },
    { month: 'Dec', small: 45, medium: 55, large: 68, xlarge: 65 }
  ];
  
  // Rekommendationer baserade på data
  const recommendations = [
    { 
      id: 1, 
      title: 'Omfördelning av platser', 
      description: 'Överväg att konvertera 5 små platser till 3 medelstora i brygga A för bättre utnyttjande.',
      impact: 'Hög', 
      difficulty: 'Medium',
      estimatedRevenue: '+45 000 kr/år'
    },
    { 
      id: 2, 
      title: 'Säsongsprissättning', 
      description: 'Öka priserna med 10% för alla platser under högsäsong (juni-augusti).',
      impact: 'Hög', 
      difficulty: 'Låg',
      estimatedRevenue: '+120 000 kr/år'
    },
    { 
      id: 3, 
      title: 'Extra serviceerbjudanden', 
      description: 'Erbjud paket med båttvätt och påfyllning av förbrukningsvaror för båtar på långtidsplatser.',
      impact: 'Medium', 
      difficulty: 'Medium',
      estimatedRevenue: '+70 000 kr/år'
    },
    { 
      id: 4, 
      title: 'Underhållsplanering', 
      description: 'Schemalägg underhåll för brygga C i oktober-november när beläggningen är lägre.',
      impact: 'Medium', 
      difficulty: 'Låg',
      estimatedRevenue: 'Kostnadsbesparing: 35 000 kr/år'
    },
    { 
      id: 5, 
      title: 'Expansion till ny brygga', 
      description: 'Utvärdera möjligheten att bygga en ny brygga med 15 stora platser baserat på hög efterfrågan.',
      impact: 'Mycket hög', 
      difficulty: 'Hög',
      estimatedRevenue: '+450 000 kr/år'
    }
  ];

  // Under-utnyttjade resurser
  const underutilizedResources = [
    { dock: 'A', slotType: 'Små platser', utilization: 45, suggestion: 'Konvertera eller erbjud specialpris vintertid' },
    { dock: 'B', slotType: 'Medelstora platser', utilization: 52, suggestion: 'Erbjud kortidspaket under lågsäsong' },
    { dock: 'D', slotType: 'Extra stora platser', utilization: 35, suggestion: 'Utvärdera prissättning eller konvertering' }
  ];

  // Visualiserar ett stapeldiagram för beläggningsdata
  const renderOccupancyChart = () => {
    const months = selectedTimeframe === 'year' ? occupancyByTypeData.map(d => d.month) : occupancyByTypeData.slice(4, 10).map(d => d.month);
    const data = selectedTimeframe === 'year' ? occupancyByTypeData : occupancyByTypeData.slice(4, 10);
    
    const maxBarHeight = 150; // Maximal stapelhöjd i pixlar
    
    return (
      <div className="h-64 flex items-end space-x-6 mt-4">
        {data.map((month, index) => (
          <div key={index} className="flex flex-col items-center flex-grow">
            <div className="w-full flex items-end justify-center space-x-1 h-48">
              <div 
                className="w-3 bg-blue-200 rounded-t-sm" 
                style={{ height: `${month.small / 100 * maxBarHeight}px` }}
                title={`Små platser: ${month.small}%`}
              ></div>
              <div 
                className="w-3 bg-blue-400 rounded-t-sm" 
                style={{ height: `${month.medium / 100 * maxBarHeight}px` }}
                title={`Medelstora platser: ${month.medium}%`}
              ></div>
              <div 
                className="w-3 bg-blue-600 rounded-t-sm" 
                style={{ height: `${month.large / 100 * maxBarHeight}px` }}
                title={`Stora platser: ${month.large}%`}
              ></div>
              <div 
                className="w-3 bg-blue-800 rounded-t-sm" 
                style={{ height: `${month.xlarge / 100 * maxBarHeight}px` }}
                title={`Extra stora platser: ${month.xlarge}%`}
              ></div>
            </div>
            <span className="text-xs text-gray-600 mt-2">{month.month}</span>
          </div>
        ))}
      </div>
    );
  };

  // Visualiserar en prestandaindikator
  const renderPerformanceIndicator = (title, value, trend, icon) => {
    const isTrendPositive = trend.startsWith('+');
    
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm text-gray-500 mb-1">{title}</p>
            <p className="text-2xl font-bold">{value}%</p>
          </div>
          <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
            {icon}
          </div>
        </div>
        <div className="mt-2 flex items-center">
          <span className={`inline-flex items-center text-xs font-medium ${isTrendPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isTrendPositive ? <ArrowUp /> : <ArrowDown />}
            <span className="ml-1">{trend}</span>
          </span>
          <span className="text-xs text-gray-500 ml-2">från föregående period</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Hamnoptimering</h1>
        <div className="flex space-x-4">
          <button className="flex items-center text-gray-600 hover:text-gray-800 bg-white px-3 py-2 rounded-lg shadow-sm">
            <Download />
            <span className="ml-1 text-sm">Exportera rapport</span>
          </button>
          <div className="flex bg-white rounded-lg shadow-sm overflow-hidden">
            <button 
              className={`px-3 py-2 text-sm ${selectedTimeframe === 'month' 
                ? 'bg-sky-600 text-white' 
                : 'bg-white text-gray-600 hover:bg-gray-50'}`}
              onClick={() => setSelectedTimeframe('month')}
            >
              Månad
            </button>
            <button 
              className={`px-3 py-2 text-sm ${selectedTimeframe === 'year' 
                ? 'bg-sky-600 text-white' 
                : 'bg-white text-gray-600 hover:bg-gray-50'}`}
              onClick={() => setSelectedTimeframe('year')}
            >
              År
            </button>
          </div>
        </div>
      </div>

      {/* KPI-indikatorer */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {renderPerformanceIndicator('Beläggningsgrad', performanceData.occupancyRate, performanceData.occupancyTrend, <BarChart />)}
        {renderPerformanceIndicator('Intäktsutnyttjande', performanceData.revenueUtilization, performanceData.revenueTrend, <DollarSign />)}
        {renderPerformanceIndicator('Kundnöjdhet', performanceData.customerSatisfaction, performanceData.satisfactionTrend, <Calendar />)}
        {renderPerformanceIndicator('Underhållseffektivitet', performanceData.maintenanceEfficiency, performanceData.maintenanceTrend, <Calendar />)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Beläggningsdiagram */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-bold text-gray-800">Beläggningsanalys per platstyp</h2>
            <div>
              <select 
                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-sky-500 focus:border-sky-500 block p-2"
                value={selectedDock}
                onChange={(e) => setSelectedDock(e.target.value)}
              >
                <option value="all">Alla bryggor</option>
                <option value="A">Brygga A</option>
                <option value="B">Brygga B</option>
                <option value="C">Brygga C</option>
                <option value="D">Brygga D</option>
              </select>
            </div>
          </div>
          {renderOccupancyChart()}
          <div className="flex justify-center space-x-6 mt-4">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-200 mr-2"></div>
              <span className="text-xs text-gray-600">Små</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-400 mr-2"></div>
              <span className="text-xs text-gray-600">Medelstora</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-600 mr-2"></div>
              <span className="text-xs text-gray-600">Stora</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-800 mr-2"></div>
              <span className="text-xs text-gray-600">Extra stora</span>
            </div>
          </div>
        </div>

        {/* Under-utnyttjade resurser */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-bold text-gray-800 mb-4">Under-utnyttjade resurser</h2>
          <div className="space-y-4">
            {underutilizedResources.map((resource, index) => (
              <div key={index} className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-800">{resource.dock}: {resource.slotType}</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    resource.utilization < 40 ? 'bg-red-100 text-red-800' : 
                    resource.utilization < 60 ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-green-100 text-green-800'
                  }`}>
                    {resource.utilization}% utnyttjande
                  </span>
                </div>
                <p className="text-sm text-gray-600">{resource.suggestion}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Optimeringsrekommendationer */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="font-bold text-gray-800 mb-4">Optimeringsrekommendationer</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rekommendation
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Inverkan
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Svårighetsgrad
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Uppskattad intäkt
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recommendations.map((rec) => (
                <tr key={rec.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{rec.title}</div>
                    <div className="text-sm text-gray-500">{rec.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      rec.impact === 'Låg' ? 'bg-blue-100 text-blue-800' : 
                      rec.impact === 'Medium' ? 'bg-green-100 text-green-800' : 
                      rec.impact === 'Hög' ? 'bg-orange-100 text-orange-800' : 
                      'bg-red-100 text-red-800'
                    }`}>
                      {rec.impact}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      rec.difficulty === 'Låg' ? 'bg-green-100 text-green-800' : 
                      rec.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' : 
                      'bg-red-100 text-red-800'
                    }`}>
                      {rec.difficulty}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {rec.estimatedRevenue}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button className="bg-sky-100 text-sky-700 hover:bg-sky-200 px-3 py-1 text-sm rounded-lg transition-colors">
                      Implementera
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insiktsmeddelande */}
      <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg flex items-start">
        <div className="mt-1 mr-3 text-blue-500">
          <Info />
        </div>
        <div>
          <h3 className="font-medium text-gray-800">Optimeringsinsikter</h3>
          <p className="text-sm text-gray-600 mt-1">
            Analysdata visar att stora och extra stora platser har konstant hög beläggning under säsongen, 
            medan mindre platser har lägre utnyttjande. Överväg att konvertera mindre använda platser 
            till större storlekar för att maximera intäkter och tillgodose efterfrågan.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Optimization;