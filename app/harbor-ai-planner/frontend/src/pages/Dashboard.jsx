import React from 'react';

// Ikoner
const Info = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="16" x2="12" y2="12"></line>
    <line x1="12" y1="8" x2="12.01" y2="8"></line>
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

const TrendingUp = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
    <polyline points="17 6 23 6 23 12"></polyline>
  </svg>
);

const Users = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
    <circle cx="9" cy="7" r="4"></circle>
    <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
  </svg>
);

// Fler ikoner som används i statistics
const MapPin = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
    <circle cx="12" cy="10" r="3"></circle>
  </svg>
);

const Anchor = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="5" r="3"></circle>
    <line x1="12" y1="22" x2="12" y2="8"></line>
    <path d="M5 12H2a10 10 0 0 0 20 0h-3"></path>
  </svg>
);

function Dashboard() {
  // Statistik data - Nu kan vi använda MapPin och Anchor eftersom de definierats ovan
  const statistics = [
    { 
      title: 'Totalt antal platser', 
      value: '120', 
      change: '+5%', 
      positive: true,
      icon: <MapPin />,
      color: 'bg-blue-500'
    },
    { 
      title: 'Upptagna platser', 
      value: '87', 
      change: '+12%', 
      positive: true,
      icon: <Anchor />,
      color: 'bg-green-500'
    },
    { 
      title: 'Intäkter denna månad', 
      value: '156 400 kr', 
      change: '+8%', 
      positive: true,
      icon: <TrendingUp />,
      color: 'bg-purple-500'
    },
    { 
      title: 'Nya kunder', 
      value: '24', 
      change: '-2%', 
      positive: false,
      icon: <Users />,
      color: 'bg-orange-500'
    },
  ];

  // Kommande båtar data
  const upcomingBoats = [
    { id: 1, name: 'Sjöbris', owner: 'Erik Lindgren', arrival: '2025-05-21', slot: 'A12', length: '8.5m', paid: true },
    { id: 2, name: 'Havsfröjd', owner: 'Anna Ström', arrival: '2025-05-22', slot: 'B04', length: '10m', paid: true },
    { id: 3, name: 'Vindseglaren', owner: 'Mikael Falk', arrival: '2025-05-23', slot: 'C09', length: '12m', paid: false },
    { id: 4, name: 'Vågsurfare', owner: 'Lisa Berg', arrival: '2025-05-24', slot: 'A15', length: '9m', paid: true },
  ];

  // Lediga platser per kategori
  const availableSlots = [
    { category: 'Små platser (< 8m)', total: 40, available: 12 },
    { category: 'Mellanstora platser (8-12m)', total: 50, available: 9 },
    { category: 'Stora platser (12-18m)', total: 25, available: 4 },
    { category: 'Extra stora platser (> 18m)', total: 5, available: 2 },
  ];

  // Senaste händelser
  const recentEvents = [
    { id: 1, time: '09:45', event: 'Ny bokning: "Sjöstjärnan" (Plats D08)', type: 'booking' },
    { id: 2, time: '11:23', event: 'Betalning mottagen: Faktura #2458', type: 'payment' },
    { id: 3, time: '12:15', event: 'Utcheckning: "Skärgårdsvind" från plats A15', type: 'checkout' },
    { id: 4, time: '13:30', event: 'Underhåll slutfört: Flytbrygga B', type: 'maintenance' },
    { id: 5, time: '14:45', event: 'Incheckning: "Havsörn" vid plats C03', type: 'checkin' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <div className="flex items-center text-sm text-gray-600">
          <Calendar />
          <span className="ml-2">Tisdag, 20 maj 2025</span>
        </div>
      </div>

      {/* Statistikkort */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statistics.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-gray-500 text-sm">{stat.title}</p>
                <p className="text-2xl font-bold mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <div className="text-white">{stat.icon}</div>
              </div>
            </div>
            <div className="mt-4 flex items-center">
              <span className={`text-xs font-medium ${stat.positive ? 'text-green-600' : 'text-red-600'}`}>
                {stat.change}
              </span>
              <span className="text-xs text-gray-500 ml-2">från föregående månad</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Kommande båtar */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="font-bold text-gray-800">Kommande båtar</h2>
          </div>
          <div className="p-4">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Båt</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ankomst</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plats</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {upcomingBoats.map(boat => (
                    <tr key={boat.id}>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{boat.name}</div>
                          <div className="text-xs text-gray-500">{boat.owner}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{boat.arrival}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{boat.slot} ({boat.length})</td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${boat.paid ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                          {boat.paid ? 'Betald' : 'Väntar på betalning'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 text-center">
              <button className="text-sm font-medium text-sky-600 hover:text-sky-800">
                Visa alla bokningar →
              </button>
            </div>
          </div>
        </div>

        {/* Lediga platser */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="font-bold text-gray-800">Tillgängliga platser</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {availableSlots.map((slot, index) => (
                <div key={index}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{slot.category}</span>
                    <span className="text-sm font-medium text-gray-700">{slot.available} / {slot.total}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-sky-600 h-2.5 rounded-full" 
                      style={{ width: `${(1 - slot.available / slot.total) * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg flex items-start">
              <div className="mt-0.5 mr-3 text-blue-500">
                <Info />
              </div>
              <p className="text-sm text-blue-700">
                Det finns <span className="font-bold">27 lediga platser</span> för kommande helg. Överväg att skicka erbjudanden till återkommande gäster.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Senaste händelser */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-bold text-gray-800">Senaste aktivitet</h2>
        </div>
        <div className="p-4">
          <ul className="divide-y divide-gray-200">
            {recentEvents.map(event => (
              <li key={event.id} className="py-3 flex items-start">
                <span className="text-sm text-gray-500 w-16">{event.time}</span>
                <span className={`inline-flex items-center justify-center h-6 w-6 rounded-full mr-3 ${
                  event.type === 'booking' ? 'bg-green-100 text-green-800' :
                  event.type === 'payment' ? 'bg-blue-100 text-blue-800' :
                  event.type === 'checkout' ? 'bg-red-100 text-red-800' :
                  event.type === 'maintenance' ? 'bg-yellow-100 text-yellow-800' : 
                  'bg-purple-100 text-purple-800'
                }`}>
                  {event.type.charAt(0).toUpperCase()}
                </span>
                <span className="text-sm text-gray-700">{event.event}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;