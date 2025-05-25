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

const Edit = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 20h9"></path>
    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
  </svg>
);

const Trash = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 6h18"></path>
    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
  </svg>
);

const ChevronDown = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9"></polyline>
  </svg>
);

function BoatList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedBoat, setExpandedBoat] = useState(null);

  // Sample data for boats
  const boatsData = [
    { 
      id: 1, 
      name: 'Matilde', 
      owner: 'Robert Green', 
      length: 8.5, 
      width: 3.2,
      type: 'Motorbåt',
      registration: 'SE-ABX-123',
      slot: 'A12',
      status: 'active',
      arrivalDate: '2025-04-15',
      departureDate: '2025-09-30',
      paidUntil: '2025-09-30',
      contactPhone: '070-123 45 67',
      contactEmail: 'maria.j@example.com',
      notes: 'Behöver el-anslutning'
    },
    { 
      id: 2, 
      name: 'Vindseglare', 
      owner: 'Anders Bergström', 
      length: 12.2, 
      width: 4.1,
      type: 'Segelbåt',
      registration: 'SE-CDY-456',
      slot: 'B08',
      status: 'active',
      arrivalDate: '2025-05-01',
      departureDate: '2025-10-15',
      paidUntil: '2025-10-15',
      contactPhone: '070-234 56 78',
      contactEmail: 'anders.b@example.com',
      notes: 'Lång mast'
    },
    { 
      id: 3, 
      name: 'Delfinen', 
      owner: 'Sophia Andersson', 
      length: 9.8, 
      width: 3.5,
      type: 'Motorbåt',
      registration: 'SE-EFG-789',
      slot: 'C04',
      status: 'active',
      arrivalDate: '2025-05-10',
      departureDate: '2025-08-25',
      paidUntil: '2025-08-25',
      contactPhone: '070-345 67 89',
      contactEmail: 'sophia.a@example.com',
      notes: ''
    },
    { 
      id: 4, 
      name: 'Vågsurfaren', 
      owner: 'Erik Lindgren', 
      length: 7.2, 
      width: 2.8,
      type: 'Motorbåt',
      registration: 'SE-HIJ-012',
      slot: 'A15',
      status: 'inactive',
      arrivalDate: '2025-04-10',
      departureDate: '2025-05-10',
      paidUntil: '2025-05-10',
      contactPhone: '070-456 78 90',
      contactEmail: 'erik.l@example.com',
      notes: 'Utcheckad'
    },
    { 
      id: 5, 
      name: 'Havsbris', 
      owner: 'Lisa Nordström', 
      length: 11.5, 
      width: 3.9,
      type: 'Segelbåt',
      registration: 'SE-KLM-345',
      slot: 'B12',
      status: 'maintenance',
      arrivalDate: '2025-03-20',
      departureDate: '2025-10-01',
      paidUntil: '2025-10-01',
      contactPhone: '070-567 89 01',
      contactEmail: 'lisa.n@example.com',
      notes: 'Under reparation till 2025-05-25'
    },
    { 
      id: 6, 
      name: 'Skärgårdsvind', 
      owner: 'Karl Svensson', 
      length: 14.2, 
      width: 4.5,
      type: 'Segelbåt',
      registration: 'SE-NOP-678',
      slot: 'D02',
      status: 'active',
      arrivalDate: '2025-05-15',
      departureDate: '2025-09-15',
      paidUntil: '2025-09-15',
      contactPhone: '070-678 90 12',
      contactEmail: 'karl.s@example.com',
      notes: 'Behöver extra förtöjning vid storm'
    },
    { 
      id: 7, 
      name: 'Solstråle', 
      owner: 'Emma Karlsson', 
      length: 6.8, 
      width: 2.5,
      type: 'Motorbåt',
      registration: 'SE-QRS-901',
      slot: 'A08',
      status: 'pending',
      arrivalDate: '2025-05-25',
      departureDate: '2025-08-15',
      paidUntil: '',
      contactPhone: '070-789 01 23',
      contactEmail: 'emma.k@example.com',
      notes: 'Väntar på betalning'
    },
  ];

  // Filter boats based on search term and status
  const filteredBoats = boatsData.filter(boat => {
    const matchesSearch = boat.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          boat.owner.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          boat.slot.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = selectedStatus === 'all' || boat.status === selectedStatus;
    
    return matchesSearch && matchesStatus;
  });

  // Pagination
  const boatsPerPage = 5;
  const totalPages = Math.ceil(filteredBoats.length / boatsPerPage);
  const indexOfLastBoat = currentPage * boatsPerPage;
  const indexOfFirstBoat = indexOfLastBoat - boatsPerPage;
  const currentBoats = filteredBoats.slice(indexOfFirstBoat, indexOfLastBoat);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Status badge
  const getStatusBadge = (status) => {
    const statusClasses = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      maintenance: 'bg-yellow-100 text-yellow-800',
      pending: 'bg-blue-100 text-blue-800'
    };
    
    const statusLabels = {
      active: 'Aktiv',
      inactive: 'Inaktiv',
      maintenance: 'Underhåll',
      pending: 'Väntar'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${statusClasses[status]}`}>
        {statusLabels[status]}
      </span>
    );
  };
  
  // Toggle expanded boat
  const toggleExpandBoat = (id) => {
    if (expandedBoat === id) {
      setExpandedBoat(null);
    } else {
      setExpandedBoat(id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Båtar</h1>
        <button className="bg-sky-600 hover:bg-sky-700 text-white py-2 px-4 rounded-lg flex items-center transition-colors">
          <Plus />
          <span className="ml-2">Lägg till båt</span>
        </button>
      </div>

      {/* Filter tools */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-grow">
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <Search />
            </div>
            <input 
              type="text" 
              className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-sky-500 focus:border-sky-500 block w-full pl-10 p-2.5"
              placeholder="Sök efter båtnamn, ägare eller platsnummer..."
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
              <option value="active">Aktiv</option>
              <option value="inactive">Inaktiv</option>
              <option value="maintenance">Underhåll</option>
              <option value="pending">Väntar</option>
            </select>
          </div>
        </div>
      </div>

      {/* Boats table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Båt
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Plats
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Storlek
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Period
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Åtgärder
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {currentBoats.map(boat => (
                <React.Fragment key={boat.id}>
                  <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => toggleExpandBoat(boat.id)}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{boat.name}</div>
                          <div className="text-sm text-gray-500">{boat.owner}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{boat.slot}</div>
                      <div className="text-sm text-gray-500">{boat.type}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{boat.length} m (längd)</div>
                      <div className="text-sm text-gray-500">{boat.width} m (bredd)</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(boat.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>{boat.arrivalDate}</div>
                      <div>till {boat.departureDate}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button 
                        className="text-sky-600 hover:text-sky-900 mr-3"
                        onClick={(e) => {
                          e.stopPropagation();
                          alert(`Redigera båt: ${boat.name}`);
                        }}
                      >
                        <Edit />
                      </button>
                      <button 
                        className="text-red-600 hover:text-red-900"
                        onClick={(e) => {
                          e.stopPropagation();
                          alert(`Ta bort båt: ${boat.name}`);
                        }}
                      >
                        <Trash />
                      </button>
                    </td>
                  </tr>
                  {expandedBoat === boat.id && (
                    <tr className="bg-gray-50">
                      <td colSpan="6" className="px-6 py-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <h4 className="font-medium text-gray-700 mb-2">Kontaktinformation</h4>
                            <p className="text-sm text-gray-600 mb-1">{boat.owner}</p>
                            <p className="text-sm text-gray-600 mb-1">Tel: {boat.contactPhone}</p>
                            <p className="text-sm text-gray-600">{boat.contactEmail}</p>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-700 mb-2">Båtinformation</h4>
                            <p className="text-sm text-gray-600 mb-1">Typ: {boat.type}</p>
                            <p className="text-sm text-gray-600 mb-1">Registrering: {boat.registration}</p>
                            <p className="text-sm text-gray-600">Mått: {boat.length}m × {boat.width}m</p>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-700 mb-2">Betalningsstatus</h4>
                            <p className="text-sm text-gray-600 mb-1">
                              Betald till: {boat.paidUntil || 'Ej betald'}
                            </p>
                            <p className="text-sm text-gray-600 mt-2">
                              <span className="font-medium">Anteckningar:</span> {boat.notes || 'Inga anteckningar'}
                            </p>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-3 flex items-center justify-between border-t border-gray-200">
            <div>
              <p className="text-sm text-gray-700">
                Visar <span className="font-medium">{indexOfFirstBoat + 1}</span> till <span className="font-medium">
                  {indexOfLastBoat > filteredBoats.length ? filteredBoats.length : indexOfLastBoat}
                </span> av <span className="font-medium">{filteredBoats.length}</span> båtar
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => paginate(currentPage > 1 ? currentPage - 1 : 1)}
                  disabled={currentPage === 1}
                  className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${
                    currentPage === 1 ? 'text-gray-300' : 'text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  Föregående
                </button>
                
                {[...Array(totalPages)].map((_, i) => (
                  <button
                    key={i}
                    onClick={() => paginate(i + 1)}
                    className={`relative inline-flex items-center px-4 py-2 border ${
                      currentPage === i + 1
                        ? 'z-10 bg-sky-50 border-sky-500 text-sky-600'
                        : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                    } text-sm font-medium`}
                  >
                    {i + 1}
                  </button>
                ))}
                
                <button
                  onClick={() => paginate(currentPage < totalPages ? currentPage + 1 : totalPages)}
                  disabled={currentPage === totalPages}
                  className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${
                    currentPage === totalPages ? 'text-gray-300' : 'text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  Nästa
                </button>
              </nav>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default BoatList;