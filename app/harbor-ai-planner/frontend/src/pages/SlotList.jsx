import React, { useState } from 'react';

// Ikoner
const Plus = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

const Search = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"></circle>
    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
  </svg>
);

const Filter = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
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

const Edit = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 20h9"></path>
    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
  </svg>
);

const Info = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="16" x2="12" y2="12"></line>
    <line x1="12" y1="8" x2="12.01" y2="8"></line>
  </svg>
);

function SlotList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedDock, setSelectedDock] = useState('all');
  const [expandedSlot, setExpandedSlot] = useState(null);

  // Sample data for slots
  const slotsData = [
    { 
      id: 1, 
      slotId: 'A01', 
      dock: 'A',
      width: 3.5, 
      length: 12,
      maxBoatWidth: 3.2,
      maxBoatLength: 11,
      depth: 2.5,
      facilities: ['El', 'Vatten', 'Wifi'],
      status: 'occupied',
      occupiedBy: 'Sjöbris (Karl Nilsson)',
      bookedUntil: '2025-09-30',
      maintenanceHistory: [
        { date: '2025-03-15', description: 'Byte av elkabel' },
        { date: '2024-11-10', description: 'Inspektion av fästen' }
      ],
      pricePerDay: 180,
      pricePerMonth: 3500
    },
    { 
      id: 2, 
      slotId: 'A02', 
      dock: 'A',
      width: 3.8, 
      length: 14,
      maxBoatWidth: 3.5,
      maxBoatLength: 13,
      depth: 2.5,
      facilities: ['El', 'Vatten', 'Wifi'],
      status: 'available',
      occupiedBy: '',
      bookedUntil: '',
      maintenanceHistory: [
        { date: '2025-04-10', description: 'Byte av pollare' }
      ],
      pricePerDay: 210,
      pricePerMonth: 4100
    },
    { 
      id: 3, 
      slotId: 'A03', 
      dock: 'A',
      width: 4.2, 
      length: 16,
      maxBoatWidth: 3.9,
      maxBoatLength: 15,
      depth: 2.8,
      facilities: ['El', 'Vatten', 'Wifi', 'Extra förtöjning'],
      status: 'reserved',
      occupiedBy: 'Havsbris (Anna Ström)',
      bookedUntil: '2025-08-15',
      maintenanceHistory: [],
      pricePerDay: 250,
      pricePerMonth: 4800
    },
    { 
      id: 4, 
      slotId: 'B01', 
      dock: 'B',
      width: 3.2, 
      length: 10,
      maxBoatWidth: 2.9,
      maxBoatLength: 9,
      depth: 2.2,
      facilities: ['El', 'Vatten'],
      status: 'maintenance',
      occupiedBy: '',
      bookedUntil: '',
      maintenanceHistory: [
        { date: '2025-05-10', description: 'Reparation av brygga' }
      ],
      pricePerDay: 160,
      pricePerMonth: 3100
    },
    { 
      id: 5, 
      slotId: 'B02', 
      dock: 'B',
      width: 3.5, 
      length: 12,
      maxBoatWidth: 3.2,
      maxBoatLength: 11,
      depth: 2.5,
      facilities: ['El', 'Vatten', 'Wifi'],
      status: 'occupied',
      occupiedBy: 'Skärgårdsdröm (Mikael Berg)',
      bookedUntil: '2025-10-15',
      maintenanceHistory: [],
      pricePerDay: 180,
      pricePerMonth: 3500
    },
    { 
      id: 6, 
      slotId: 'C01', 
      dock: 'C',
      width: 5.0, 
      length: 20,
      maxBoatWidth: 4.7,
      maxBoatLength: 19,
      depth: 3.5,
      facilities: ['El', 'Vatten', 'Wifi', 'Extra förtöjning', 'Lås'],
      status: 'occupied',
      occupiedBy: 'Vindseglare (Sofia Karlsson)',
      bookedUntil: '2025-09-01',
      maintenanceHistory: [
        { date: '2025-02-20', description: 'Förstärkning av brygga' },
        { date: '2024-12-05', description: 'Byte av eluttag' }
      ],
      pricePerDay: 350,
      pricePerMonth: 6500
    },
    { 
      id: 7, 
      slotId: 'C02', 
      dock: 'C',
      width: 4.8, 
      length: 18,
      maxBoatWidth: 4.5,
      maxBoatLength: 17,
      depth: 3.2,
      facilities: ['El', 'Vatten', 'Wifi', 'Extra förtöjning'],
      status: 'available',
      occupiedBy: '',
      bookedUntil: '',
      maintenanceHistory: [],
      pricePerDay: 320,
      pricePerMonth: 6000
    },
    { 
      id: 8, 
      slotId: 'D01', 
      dock: 'D',
      width: 6.0, 
      length: 25,
      maxBoatWidth: 5.7,
      maxBoatLength: 24,
      depth: 4.0,
      facilities: ['El', 'Vatten', 'Wifi', 'Extra förtöjning', 'Lås', 'Bevakning'],
      status: 'occupied',
      occupiedBy: 'Havskryssaren (Johan Ekman)',
      bookedUntil: '2025-10-30',
      maintenanceHistory: [
        { date: '2025-01-15', description: 'Installation av nytt låssystem' }
      ],
      pricePerDay: 450,
      pricePerMonth: 8500
    },
    { 
      id: 9, 
      slotId: 'D02', 
      dock: 'D',
      width: 5.5, 
      length: 22,
      maxBoatWidth: 5.2,
      maxBoatLength: 21,
      depth: 3.8,
      facilities: ['El', 'Vatten', 'Wifi', 'Extra förtöjning', 'Lås'],
      status: 'available',
      occupiedBy: '',
      bookedUntil: '',
      maintenanceHistory: [],
      pricePerDay: 400,
      pricePerMonth: 7800
    },
  ];

  // Filter slots based on search term, status, dock, etc.
  const filteredSlots = slotsData.filter(slot => {
    const matchesSearch = slot.slotId.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (slot.occupiedBy && slot.occupiedBy.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = selectedStatus === 'all' || slot.status === selectedStatus;
    
    const matchesDock = selectedDock === 'all' || slot.dock === selectedDock;
    
    return matchesSearch && matchesStatus && matchesDock;
  });

  // Toggle expanded slot
  const toggleExpandSlot = (id) => {
    if (expandedSlot === id) {
      setExpandedSlot(null);
    } else {
      setExpandedSlot(id);
    }
  };

  // Status badge
  const getStatusBadge = (status) => {
    const statusClasses = {
      available: 'bg-green-100 text-green-800',
      occupied: 'bg-red-100 text-red-800',
      reserved: 'bg-blue-100 text-blue-800',
      maintenance: 'bg-yellow-100 text-yellow-800'
    };
    
    const statusLabels = {
      available: 'Tillgänglig',
      occupied: 'Upptagen',
      reserved: 'Reserverad',
      maintenance: 'Underhåll'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${statusClasses[status]}`}>
        {statusLabels[status]}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Båtplatser</h1>
        <button className="bg-sky-600 hover:bg-sky-700 text-white py-2 px-4 rounded-lg flex items-center transition-colors">
          <Plus />
          <span className="ml-2">Lägg till plats</span>
        </button>
      </div>

      {/* Filter tools */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <Search />
            </div>
            <input 
              type="text" 
              className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-sky-500 focus:border-sky-500 block w-full pl-10 p-2.5"
              placeholder="Sök efter plats eller båt..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter />
            <select 
              className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-sky-500 focus:border-sky-500 block w-full p-2.5"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              <option value="all">Alla statusar</option>
              <option value="available">Tillgänglig</option>
              <option value="occupied">Upptagen</option>
              <option value="reserved">Reserverad</option>
              <option value="maintenance">Underhåll</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <Filter />
            <select 
              className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-sky-500 focus:border-sky-500 block w-full p-2.5"
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
          
          <div className="flex items-center gap-2">
            <Calendar />
            <input 
              type="date" 
              className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-sky-500 focus:border-sky-500 block w-full p-2.5"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              placeholder="Välj datum för att se tillgänglighet"
            />
          </div>
        </div>
      </div>

      {/* Slots grid view */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSlots.map(slot => (
          <div 
            key={slot.id} 
            className="bg-white rounded-lg shadow overflow-hidden hover:shadow-md transition-shadow"
          >
            <div 
              className={`px-4 py-3 ${
                slot.status === 'available' ? 'bg-green-50 border-b border-green-100' :
                slot.status === 'occupied' ? 'bg-red-50 border-b border-red-100' :
                slot.status === 'reserved' ? 'bg-blue-50 border-b border-blue-100' :
                'bg-yellow-50 border-b border-yellow-100'
              }`}
            >
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-gray-800">Plats {slot.slotId}</h3>
                {getStatusBadge(slot.status)}
              </div>
              <p className="text-sm text-gray-600">Brygga {slot.dock}</p>
            </div>
            
            <div className="p-4">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-xs text-gray-500">MÅTT</p>
                  <p className="text-sm">
                    <span className="font-medium">{slot.width} × {slot.length} m</span>
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">DJUP</p>
                  <p className="text-sm">
                    <span className="font-medium">{slot.depth} m</span>
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">MAX BÅTSTORLEK</p>
                  <p className="text-sm">
                    <span className="font-medium">{slot.maxBoatWidth} × {slot.maxBoatLength} m</span>
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">PRIS</p>
                  <p className="text-sm">
                    <span className="font-medium">{slot.pricePerDay} kr/dag</span>
                  </p>
                </div>
              </div>
              
              {slot.status === 'occupied' || slot.status === 'reserved' ? (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 mb-1">UPPTAGEN AV</p>
                  <p className="text-sm font-medium">{slot.occupiedBy}</p>
                  <p className="text-xs text-gray-500 mt-2">BOKAD TILL</p>
                  <p className="text-sm">{slot.bookedUntil}</p>
                </div>
              ) : null}
              
              <div className="flex flex-wrap gap-2 mb-4">
                {slot.facilities.map((facility, index) => (
                  <span 
                    key={index} 
                    className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full"
                  >
                    {facility}
                  </span>
                ))}
              </div>
              
              <div className="flex justify-between">
                <button 
                  className="text-sky-600 hover:text-sky-800 text-sm font-medium"
                  onClick={() => toggleExpandSlot(slot.id)}
                >
                  {expandedSlot === slot.id ? 'Visa mindre' : 'Visa mer'}
                </button>
                <button className="text-sky-600 hover:text-sky-800">
                  <Edit />
                </button>
              </div>
              
              {expandedSlot === slot.id && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="font-medium text-gray-700 mb-2">Underhållshistorik</h4>
                  {slot.maintenanceHistory.length > 0 ? (
                    <ul className="space-y-2">
                      {slot.maintenanceHistory.map((maintenance, index) => (
                        <li key={index} className="text-sm">
                          <span className="text-gray-500">{maintenance.date}:</span> {maintenance.description}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-500">Ingen underhållshistorik tillgänglig</p>
                  )}
                  
                  <div className="mt-4 flex justify-between">
                    <button className="bg-sky-100 text-sky-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-sky-200 transition-colors">
                      Boka plats
                    </button>
                    <button className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
                      Rapportera underhåll
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {filteredSlots.length === 0 && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="flex justify-center mb-4 text-gray-400">
            <Info />
          </div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">Inga platser hittades</h3>
          <p className="text-gray-600">Prova att ändra dina filteralternativ eller sökterm.</p>
        </div>
      )}
    </div>
  );
}

export default SlotList;