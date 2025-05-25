import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import BoatList from './pages/BoatList';
import SlotList from './pages/SlotList';
import Optimization from './pages/Optimization';
import Visualization from './pages/Visualization';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  // Funktion för att rendera aktuell sida baserat på navigationsvalet
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'boats':
        return <BoatList />;
      case 'slots':
        return <SlotList />;
      case 'optimize':
        return <Optimization />;
      case 'visualization':
        return <Visualization />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout currentPage={currentPage} setCurrentPage={setCurrentPage}>
      {renderPage()}
    </Layout>
  );
}

export default App;