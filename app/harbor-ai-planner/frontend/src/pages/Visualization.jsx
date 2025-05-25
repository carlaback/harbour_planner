import { useState, useEffect } from 'react';
import { fetchAllSlots, fetchAllDocks, updateSlotStatus } from '../services/api';

function Visualization() {
  const [slots, setSlots] = useState([]);
  const [docks, setDocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  // Ny state för hover
  const [hoveredSlot, setHoveredSlot] = useState(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [stats, setStats] = useState({
    totalGuest: 0,
    availableGuest: 0,
    totalFlex: 0,
    availableFlex: 0
  });

  // NYA STATES för optimering
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [showOptimization, setShowOptimization] = useState(false);
  const [strategyPlacements, setStrategyPlacements] = useState({});

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // Hämta både bryggor och platser
        const [slotsRes, docksRes] = await Promise.all([
          fetchAllSlots(),
          fetchAllDocks()
        ]);
        
        setSlots(slotsRes.data);
        setDocks(docksRes.data);
        
        // Beräkna statistik
        const guestSlots = slotsRes.data.filter(slot => slot.slot_type === 'guest');
        const flexSlots = slotsRes.data.filter(slot => slot.slot_type === 'flex');
        
        setStats({
          totalGuest: guestSlots.length,
          availableGuest: guestSlots.filter(slot => slot.status === 'available').length,
          totalFlex: flexSlots.length,
          availableFlex: flexSlots.filter(slot => slot.status === 'available').length
        });
        
        setError(null);
      } catch (err) {
        console.error('Fel vid hämtning av data:', err);
        setError('Kunde inte ladda hamndata. Försök igen senare.');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Förbättrade event listeners
    const handleNavigation = (event) => {
      console.log('📍 Navigation event received:', event.detail);
      if (event.detail === 'visualization') {
        loadOptimizationResult();
      }
    };

    const handleOptimizationComplete = (event) => {
      console.log('✅ Optimization complete event received:', event.detail);
      if (event.detail?.result) {
        setOptimizationResult(event.detail.result);
        setShowOptimization(true);
        
        // Sätt bästa strategin som standard
        if (event.detail.result.auto_selected_best?.name) {
          setSelectedStrategy(event.detail.result.auto_selected_best.name);
        }
        
        // Extrahera placeringarna för varje strategi
        const placements = {};
        if (event.detail.result.strategy_results) {
          Object.entries(event.detail.result.strategy_results).forEach(([strategyName, strategyData]) => {
            if (strategyData.placements) {
              placements[strategyName] = strategyData.placements;
            }
          });
          setStrategyPlacements(placements);
        }
      }
    };

    const handleMapDataUpdate = (event) => {
      console.log('🗺️ Map data update event received:', event.detail);
      if (event.detail?.result) {
        setOptimizationResult(event.detail.result);
        if (event.detail.selectedStrategy) {
          setSelectedStrategy(event.detail.selectedStrategy);
        }
      }
    };

    // Lägg till event listeners
    window.addEventListener('navigate', handleNavigation);
    window.addEventListener('optimizationComplete', handleOptimizationComplete);
    window.addEventListener('updateMapData', handleMapDataUpdate);

    // Kolla om det finns optimeringsresultat när sidan laddas
    loadOptimizationResult();

    return () => {
      window.removeEventListener('navigate', handleNavigation);
      window.removeEventListener('optimizationComplete', handleOptimizationComplete);
      window.removeEventListener('updateMapData', handleMapDataUpdate);
    };
  }, []);

  // Ladda optimeringsresultat från localStorage
  const loadOptimizationResult = () => {
    try {
      const savedResult = localStorage.getItem('optimizationResult');
      if (savedResult) {
        const result = JSON.parse(savedResult);
        console.log('📊 Loading optimization result from localStorage:', result);
        
        setOptimizationResult(result);
        setShowOptimization(true);
        
        // Extrahera placeringarna för varje strategi
        const placements = {};
        if (result.strategy_results) {
          Object.entries(result.strategy_results).forEach(([strategyName, strategyData]) => {
            if (strategyData.placements) {
              placements[strategyName] = strategyData.placements;
            }
          });
        }
        setStrategyPlacements(placements);
        
        // Välj bästa strategin som standard
        if (result.auto_selected_best) {
          setSelectedStrategy(result.auto_selected_best.name);
        }
        
        console.log('📋 Extracted strategy placements:', Object.keys(placements));
      }
    } catch (err) {
      console.error('Kunde inte ladda optimeringsresultat:', err);
    }
  };

  // Växla mellan standardvy och optimeringsvy
  const toggleOptimizationView = () => {
    setShowOptimization(!showOptimization);
    if (!showOptimization && optimizationResult?.auto_selected_best) {
      setSelectedStrategy(optimizationResult.auto_selected_best.name);
    } else {
      setSelectedStrategy(null);
    }
  };

  // Funktion för att bestämma färg baserat på platsens typ och status
  const getSlotColor = (slot) => {
    // Om vi visar optimeringsresultat
    if (showOptimization && selectedStrategy && strategyPlacements[selectedStrategy]) {
      const placement = strategyPlacements[selectedStrategy].find(p => p.slot_id === slot.id);
      if (placement) {
        // Plats används av en båt i den valda strategin
        return 'fill-blue-500 stroke-blue-700';
      }
    }
    
    // Permanenta platser är alltid röda
    if (slot.slot_type === 'permanent') {
      return 'fill-red-600 stroke-red-800';
    }
    
    // För gäst- och flexplatser beror färgen på status
    switch (slot.status) {
      case 'available':
        return 'fill-green-500 stroke-green-700';
      case 'occupied':
        return 'fill-red-500 stroke-red-700';
      case 'reserved':
        return 'fill-yellow-500 stroke-yellow-700';
      case 'maintenance':
        return 'fill-gray-500 stroke-gray-700';
      default:
        return 'fill-blue-300 stroke-blue-500';
    }
  };

  // Hämta båtinformation för en plats
  const getBoatInfoForSlot = (slotId) => {
    if (!showOptimization || !selectedStrategy || !strategyPlacements[selectedStrategy]) {
      return null;
    }
    
    return strategyPlacements[selectedStrategy].find(p => p.slot_id === slotId);
  };

  // Funktioner för hover (oförändrade)
  const handleMouseEnter = (slot, e) => {
    setHoveredSlot(slot);
    updateMousePosition(e);
  };

  const handleMouseLeave = () => {
    setHoveredSlot(null);
  };

  const handleMouseMove = (e) => {
    if (hoveredSlot) {
      updateMousePosition(e);
    }
  };

  const updateMousePosition = (e) => {
    const svg = e.currentTarget.closest('svg');
    const rect = svg.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setMousePosition({ x, y });
  };

  const handleSlotClick = (slot) => {
    if (slot.slot_type === 'permanent') {
      return;
    }
    setSelectedSlot(slot);
  };

  const handleStatusChange = async (id, status) => {
    try {
      setSlots(prevSlots => 
        prevSlots.map(slot => 
          slot.id === id ? { ...slot, status } : slot
        )
      );
      
      if (selectedSlot && selectedSlot.id === id) {
        setSelectedSlot(prev => ({ ...prev, status }));
      }
      
      await updateSlotStatus(id, status);
      
      const updatedSlots = slots.map(slot => 
        slot.id === id ? { ...slot, status } : slot
      );
      
      const guestSlots = updatedSlots.filter(slot => slot.slot_type === 'guest');
      const flexSlots = updatedSlots.filter(slot => slot.slot_type === 'flex');
      
      setStats({
        totalGuest: guestSlots.length,
        availableGuest: guestSlots.filter(slot => slot.status === 'available').length,
        totalFlex: flexSlots.length,
        availableFlex: flexSlots.filter(slot => slot.status === 'available').length
      });
      
    } catch (error) {
      console.error('Fel vid uppdatering av status:', error);
    }
  };

  if (loading) return <div className="text-center p-8">Laddar hamndata...</div>;
  if (error) return <div className="text-red-600 p-8">{error}</div>;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Hamnöversikt</h2>
        
        {/* Växla mellan standardvy och optimeringsvy */}
        {optimizationResult && (
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleOptimizationView}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                showOptimization 
                  ? 'bg-blue-500 text-white hover:bg-blue-600' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showOptimization ? '📊 Optimeringsvy' : '🗺️ Standardvy'}
            </button>
            
            {showOptimization && (
              <button
                onClick={() => {
                  localStorage.removeItem('optimizationResult');
                  setOptimizationResult(null);
                  setShowOptimization(false);
                  setSelectedStrategy(null);
                }}
                className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                ✖️ Rensa
              </button>
            )}
          </div>
        )}
      </div>

      {/* Optimeringsstrategier - tabs */}
      {showOptimization && optimizationResult && (
        <div className="mb-6 bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-bold mb-3">Välj Strategi att Visa:</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(optimizationResult.evaluations || {})
              .sort(([,a], [,b]) => b.boats_placed - a.boats_placed)
              .map(([strategyName, evaluation]) => (
                <button
                  key={strategyName}
                  onClick={() => setSelectedStrategy(strategyName)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    selectedStrategy === strategyName
                      ? 'bg-blue-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  } ${strategyName === optimizationResult.auto_selected_best?.name ? 'ring-2 ring-green-400' : ''}`}
                >
                  <div className="text-sm">
                    {strategyName}
                    {strategyName === optimizationResult.auto_selected_best?.name && ' ⭐'}
                  </div>
                  <div className="text-xs opacity-75">
                    {evaluation.boats_placed}/{evaluation.total_boats} båtar
                  </div>
                </button>
              ))}
          </div>
          
          {selectedStrategy && optimizationResult.evaluations[selectedStrategy] && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <h4 className="font-bold text-blue-800 mb-2">
                Strategi: {selectedStrategy}
                {selectedStrategy === optimizationResult.auto_selected_best?.name && ' (Bäst) ⭐'}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium">Placerade båtar:</span>
                  <div className="text-lg font-bold text-blue-600">
                    {optimizationResult.evaluations[selectedStrategy].boats_placed} / {optimizationResult.evaluations[selectedStrategy].total_boats}
                  </div>
                </div>
                <div>
                  <span className="font-medium">Placeringsgrad:</span>
                  <div className="text-lg font-bold text-green-600">
                    {(optimizationResult.evaluations[selectedStrategy].placement_rate * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="font-medium">Utnyttjandegrad:</span>
                  <div className="text-lg font-bold text-orange-600">
                    {(optimizationResult.evaluations[selectedStrategy].utilization * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="font-medium">Poäng:</span>
                  <div className="text-lg font-bold text-purple-600">
                    {(optimizationResult.evaluations[selectedStrategy].score * 100).toFixed(1)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Sammanfattning av platser */}
      {!showOptimization && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium">Gästplatser</h3>
            <p className="text-2xl font-bold text-green-600">{stats.availableGuest} / {stats.totalGuest}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium">Flexplatser</h3>
            <p className="text-2xl font-bold text-green-600">{stats.availableFlex} / {stats.totalFlex}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium">Totalt lediga</h3>
            <p className="text-2xl font-bold text-green-600">{stats.availableGuest + stats.availableFlex}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium">Totalt antal platser</h3>
            <p className="text-2xl font-bold">{slots.length}</p>
          </div>
        </div>
      )}
      
      {/* Förklaring av färgkoder */}
      <div className="flex flex-wrap gap-4 mb-6">
        {showOptimization ? (
          // Färgkoder för optimeringsvy
          <>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-500 mr-2"></div>
              <span>Båt placerad (vald strategi)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-500 mr-2"></div>
              <span>Ledig plats</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-600 mr-2"></div>
              <span>Permanent plats</span>
            </div>
          </>
        ) : (
          // Standard färgkoder
          <>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-500 mr-2"></div>
              <span>Ledig</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-500 mr-2"></div>
              <span>Upptagen/Permanent</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-yellow-500 mr-2"></div>
              <span>Reserverad</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-gray-500 mr-2"></div>
              <span>Underhåll</span>
            </div>
          </>
        )}
      </div>
      
      <div className="marina-map bg-blue-50 rounded-lg p-4 border border-blue-200 shadow-inner overflow-auto">
        <svg 
          width="1200" 
          height="1600"  
          viewBox="0 0 1200 1600" 
          onMouseMove={handleMouseMove}
        >
          {/* Rita vatten som bakgrund */}
          <rect
            x="0"
            y="0"
            width="1200"
            height="1600"
            className="fill-blue-300"
          />
          
          {/* Rita bryggorna först (bakgrund) */}
          {docks.map(dock => (
            <rect
              key={`dock-${dock.id}`}
              className="fill-amber-800 stroke-amber-900"
              x={dock.position_x}
              y={dock.position_y}
              width={dock.width}
              height={dock.length}
            >
              <title>Brygga {dock.name}</title>
            </rect>
          ))}
          
          {/* Rita båtplatserna ovanpå bryggorna */}
          {slots.map(slot => {
            const boatInfo = getBoatInfoForSlot(slot.id);
            return (
              <g key={`slot-${slot.id}`}>
                <rect
                  className={`${getSlotColor(slot)} cursor-pointer transition-all duration-300 hover:opacity-80`}
                  x={slot.position_x}
                  y={slot.position_y}
                  width={slot.width}
                  height={slot.length}
                  onClick={() => handleSlotClick(slot)}
                  onMouseEnter={(e) => handleMouseEnter(slot, e)}
                  onMouseLeave={handleMouseLeave}
                >
                  <title>
                    Plats {slot.id} - {slot.slot_type === 'permanent' ? 'Permanent' : 
                                      slot.slot_type === 'flex' ? 'Flexplats' : 'Gästplats'}
                    {boatInfo ? ` - Båt ID: ${boatInfo.boat_id}` : ''}
                  </title>
                </rect>
                
                {/* Text för platsnummer */}
                <text
                  x={slot.position_x + slot.width / 2}
                  y={slot.position_y + slot.length / 2}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="fill-white text-xs font-bold pointer-events-none"
                  style={{ fontSize: Math.min(slot.width, slot.length) * 0.3 }}
                >
                  {boatInfo ? `B${boatInfo.boat_id}` : slot.id}
                </text>
              </g>
            );
          })}
          
          {/* Special text för drop-in områden */}
          {slots.filter(slot => slot.name?.includes('DROP-IN')).map(slot => (
            <text
              key={`text-${slot.id}`}
              x={slot.position_x + slot.width / 2}
              y={slot.position_y + slot.length / 2}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-black text-lg font-bold pointer-events-none"
            >
              {slot.name}
            </text>
          ))}
          
          {/* Text för "Bastu" */}
          {slots.filter(slot => slot.name?.includes('Båstupläggning')).map(slot => (
            <text
              key={`text-${slot.id}`}
              x={slot.position_x + 20}
              y={slot.position_y + 50}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-black text-lg font-bold pointer-events-none"
              transform="rotate(90, 710, 1045)"
            >
              Båstupläggning
            </text>
          ))}
        </svg>
        
        {/* Tooltip som visas vid hover */}
        {hoveredSlot && (
          <div 
            className="absolute bg-white p-3 rounded-lg shadow-lg border border-gray-200 z-10"
            style={{ 
              left: `${mousePosition.x + 20}px`, 
              top: `${mousePosition.y - 10}px` 
            }}
          >
            <h3 className="font-bold text-lg border-b pb-1 mb-2">
              Plats {hoveredSlot.id}
              {showOptimization && getBoatInfoForSlot(hoveredSlot.id) && (
                <span className="text-blue-600"> - Båt {getBoatInfoForSlot(hoveredSlot.id).boat_id}</span>
              )}
            </h3>
            <p><span className="font-semibold">Typ:</span> {
              hoveredSlot.slot_type === 'guest' ? 'Gästplats' : 
              hoveredSlot.slot_type === 'flex' ? 'Flexplats' : 
              hoveredSlot.slot_type === 'permanent' ? 'Permanent plats' : 
              hoveredSlot.slot_type === 'guest_drop_in' ? 'Drop-in område' : 
              'Annan'
            }</p>
            
            {/* Visa båtinformation om optimeringsvy är aktiv */}
            {showOptimization && getBoatInfoForSlot(hoveredSlot.id) && (
              <div className="mt-2 p-2 bg-blue-50 rounded">
                <p className="font-semibold text-blue-800">🚤 Placerad båt:</p>
                <p><span className="font-semibold">Båt ID:</span> {getBoatInfoForSlot(hoveredSlot.id).boat_id}</p>
                <p><span className="font-semibold">Ankomst:</span> {new Date(getBoatInfoForSlot(hoveredSlot.id).start_time).toLocaleDateString('sv-SE')}</p>
                <p><span className="font-semibold">Avresa:</span> {new Date(getBoatInfoForSlot(hoveredSlot.id).end_time).toLocaleDateString('sv-SE')}</p>
                <p><span className="font-semibold">Strategi:</span> {getBoatInfoForSlot(hoveredSlot.id).strategy_name}</p>
              </div>
            )}
            
            {!showOptimization && (
              <p><span className="font-semibold">Status:</span> <span className={
                hoveredSlot.status === 'available' ? 'text-green-600' : 
                hoveredSlot.status === 'occupied' ? 'text-red-600' : 
                hoveredSlot.status === 'reserved' ? 'text-yellow-600' : 'text-gray-600'
              }>{
                hoveredSlot.status === 'available' ? 'Ledig' : 
                hoveredSlot.status === 'occupied' ? 'Upptagen' : 
                hoveredSlot.status === 'reserved' ? 'Reserverad' : 'Underhåll'
              }</span></p>
            )}
            
            <p><span className="font-semibold">Storlek:</span> {hoveredSlot.width / 10}m × {hoveredSlot.length / 10}m</p>
            <p><span className="font-semibold">Djup:</span> {hoveredSlot.depth || 'Ej angivet'} m</p>
            <p><span className="font-semibold">Max båtbredd:</span> {hoveredSlot.max_width || 'Ej angivet'} m</p>
            <p><span className="font-semibold">Pris per dag:</span> {hoveredSlot.price_per_day || 0} kr</p>
            <p><span className="font-semibold">Brygga:</span> {hoveredSlot.dock_id}</p>
          </div>
        )}
      </div>
      
      {/* Information om vald plats (klickad plats) - endast i standardvy */}
      {!showOptimization && selectedSlot && (
        <div className="mt-4 bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold">Plats {selectedSlot.id}</h3>
          <p>Typ: {
            selectedSlot.slot_type === 'guest' ? 'Gästplats' : 
            selectedSlot.slot_type === 'flex' ? 'Flexplats' : 
            selectedSlot.slot_type === 'permanent' ? 'Permanent plats' : 
            selectedSlot.slot_type === 'guest_drop_in' ? 'Drop-in område' : 
            'Annan'
          }</p>
          <p>Status: <span className={`font-medium ${
            selectedSlot.status === 'available' ? 'text-green-600' : 
            selectedSlot.status === 'occupied' ? 'text-red-600' : 
            selectedSlot.status === 'reserved' ? 'text-yellow-600' : 'text-gray-600'
          }`}>{
            selectedSlot.status === 'available' ? 'Ledig' : 
            selectedSlot.status === 'occupied' ? 'Upptagen' : 
            selectedSlot.status === 'reserved' ? 'Reserverad' : 'Underhåll'
          }</span></p>
          <p>Storlek: {selectedSlot.width / 10}m × {selectedSlot.length / 10}m</p>
          <p>Djup: {selectedSlot.depth || 'Ej angivet'} m</p>
          <p>Max båtbredd: {selectedSlot.max_width || 'Ej angivet'} m</p>
          <p>Pris per dag: {selectedSlot.price_per_day || 0} kr</p>
          <p>Brygga: {selectedSlot.dock_id}</p>
          
          {/* Knappar för att ändra status (endast för gäst- och flexplatser) */}
          {selectedSlot.slot_type !== 'permanent' && (
            <div className="mt-4 flex flex-wrap gap-2">
              <button 
                className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
                onClick={() => handleStatusChange(selectedSlot.id, 'available')}
                disabled={selectedSlot.status === 'available'}
              >
                Markera som ledig
              </button>
              <button 
                className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
                onClick={() => handleStatusChange(selectedSlot.id, 'occupied')}
                disabled={selectedSlot.status === 'occupied'}
              >
                Markera som upptagen
              </button>
              <button 
                className="bg-yellow-500 text-white px-3 py-1 rounded hover:bg-yellow-600"
                onClick={() => handleStatusChange(selectedSlot.id, 'reserved')}
                disabled={selectedSlot.status === 'reserved'}
              >
                Markera som reserverad
              </button>
              <button 
                className="bg-gray-500 text-white px-3 py-1 rounded hover:bg-gray-600"
                onClick={() => handleStatusChange(selectedSlot.id, 'maintenance')}
                disabled={selectedSlot.status === 'maintenance'}
              >
                Markera som underhåll
              </button>
            </div>
          )}
          
          <button 
            className="mt-3 bg-gray-200 text-gray-800 px-3 py-1 rounded hover:bg-gray-300"
            onClick={() => setSelectedSlot(null)}
          >
            Stäng
          </button>
        </div>
      )}

      {/* Optimeringsresultat sammanfattning */}
      {showOptimization && optimizationResult && (
        <div className="mt-6 bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-bold mb-3">📊 Optimeringssammanfattning</h3>
          
          {optimizationResult.auto_selected_best && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-bold text-green-800 mb-2">
                🏆 Automatiskt Vald Bästa Strategi: {optimizationResult.auto_selected_best.name}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium">Placerade båtar:</span>
                  <div className="text-xl font-bold text-green-600">
                    {optimizationResult.auto_selected_best.evaluation.boats_placed} / {optimizationResult.auto_selected_best.evaluation.total_boats}
                  </div>
                </div>
                <div>
                  <span className="font-medium">Placeringsgrad:</span>
                  <div className="text-xl font-bold text-blue-600">
                    {(optimizationResult.auto_selected_best.evaluation.placement_rate * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="font-medium">Utnyttjandegrad:</span>
                  <div className="text-xl font-bold text-orange-600">
                    {(optimizationResult.auto_selected_best.evaluation.utilization * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="font-medium">Poäng:</span>
                  <div className="text-xl font-bold text-purple-600">
                    {(optimizationResult.auto_selected_best.evaluation.score * 100).toFixed(1)}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="text-sm text-gray-600">
            <p className="mb-2">
              <strong>💡 Tips:</strong> Klicka på strategiknapparna ovan för att växla mellan olika placeringslösningar. 
              Blå platser visar var båtar har placerats enligt den valda strategin.
            </p>
            <p>
              <strong>🗺️ Kartnavigation:</strong> Hovra över platser för detaljerad information, inklusive båtinformation när optimeringsvy är aktiv.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Visualization;