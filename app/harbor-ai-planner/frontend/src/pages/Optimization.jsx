import React, { useState, useEffect } from 'react';
import { 
  Container, Typography, Paper, Box, Button, CircularProgress, 
  Grid, Alert, LinearProgress
} from '@mui/material';
import api from '../services/api';

export default function Optimization() {
  const [loading, setLoading] = useState(false);
  const [strategies, setStrategies] = useState([]);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [error, setError] = useState('');
  const [currentStrategy, setCurrentStrategy] = useState('');
  const [progress, setProgress] = useState(0);

  // Hämta tillgängliga strategier vid laddning
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await api.getStrategies();
        setStrategies(response.data);
      } catch (err) {
        console.error("Error fetching strategies:", err);
        setError('Kunde inte hämta strategier. Kontrollera att backend-servern körs.');
      }
    };
    
    fetchStrategies();
  }, []);

  // Hitta den bästa strategin baserat på antal placerade båtar
  const findBestStrategy = (evaluations) => {
    let bestStrategy = null;
    let maxBoatsPlaced = 0;
    
    Object.entries(evaluations).forEach(([strategyName, evaluation]) => {
      if (evaluation.boats_placed > maxBoatsPlaced) {
        maxBoatsPlaced = evaluation.boats_placed;
        bestStrategy = {
          name: strategyName,
          evaluation: evaluation
        };
      }
    });
    
    return bestStrategy;
  };

  // Kör automatisk optimering med alla strategier
  const handleRunOptimization = async () => {
    setLoading(true);
    setError('');
    setProgress(0);
    setCurrentStrategy('');
    
    try {
      // Hämta alla strateginamn
      const allStrategyNames = strategies.map(strategy => strategy.name);
      
      if (allStrategyNames.length === 0) {
        setError('Inga strategier tillgängliga för optimering.');
        return;
      }

      // Uppdatera progress när vi börjar
      setCurrentStrategy('Förbereder optimering...');
      setProgress(10);

      // Kör optimering med alla strategier
      setCurrentStrategy('Kör optimering med alla strategier...');
      setProgress(30);
      
      const response = await api.runOptimization(allStrategyNames);
      setProgress(70);
      
      // Hitta den bästa strategin
      setCurrentStrategy('Analyserar resultat...');
      const bestStrategy = findBestStrategy(response.data.evaluations || {});
      
      // VIKTIGT: Konvertera data till format som Visualization förväntar sig
      const enhancedResult = {
        ...response.data,
        auto_selected_best: bestStrategy,
        // Lägg till strategy_results för bakåtkompatibilitet med din Visualization
        strategy_results: {},
        gpt_analysis: {
          ...response.data.gpt_analysis,
          best_strategy: bestStrategy?.name || 'Ingen strategi kunde utvärderas',
          auto_optimization: true,
          boats_placed: bestStrategy?.evaluation?.boats_placed || 0,
          total_boats: bestStrategy?.evaluation?.total_boats || 0,
          placement_rate: bestStrategy?.evaluation?.placement_rate || 0,
          recommendations: [
            `Automatisk optimering valde strategin "${bestStrategy?.name}" som placerar flest båtar (${bestStrategy?.evaluation?.boats_placed || 0} av ${bestStrategy?.evaluation?.total_boats || 0}).`,
            ...(response.data.gpt_analysis?.recommendations || [])
          ]
        }
      };

      // Konvertera strategies-data till strategy_results format för din Visualization
      if (response.data.strategies) {
        Object.entries(response.data.strategies).forEach(([strategyName, placements]) => {
          enhancedResult.strategy_results[strategyName] = {
            placements: placements.map(placement => ({
              boat_id: placement.boat_id,
              slot_id: placement.slot_id,
              start_time: placement.start_time,
              end_time: placement.end_time,
              strategy_name: strategyName
            }))
          };
        });
      }
      
      setOptimizationResult(enhancedResult);
      setProgress(100);
      setCurrentStrategy('Optimering slutförd!');
      
      // Spara optimeringsresultat så visualization kan komma åt dem
      localStorage.setItem('optimizationResult', JSON.stringify(enhancedResult));
      localStorage.setItem('lastOptimization', new Date().toISOString());
      localStorage.setItem('lastOptimizationStrategy', bestStrategy?.name || 'Okänd');
      localStorage.setItem('lastOptimizationBoats', bestStrategy?.evaluation?.boats_placed || 0);
      
      // Skicka event för att notifiera Visualization
      window.dispatchEvent(new CustomEvent('optimizationComplete', { 
        detail: { 
          result: enhancedResult,
          bestStrategy: bestStrategy,
          timestamp: new Date().toISOString()
        } 
      }));
      
      console.log('✅ Optimization completed and saved:', {
        strategies: Object.keys(enhancedResult.strategy_results || {}),
        bestStrategy: bestStrategy?.name,
        evaluations: Object.keys(enhancedResult.evaluations || {})
      });
      
    } catch (err) {
      console.error("Error running optimization:", err);
      setError('Ett fel uppstod vid optimering. Kontrollera att API-servern är igång.');
      setProgress(0);
      setCurrentStrategy('');
    } finally {
      setLoading(false);
    }
  };

  // Visa optimeringsresultat på kartan
  const handleViewOnMap = () => {
    if (optimizationResult) {
      console.log('🗺️ Navigating to visualization with data:', {
        hasStrategyResults: !!optimizationResult.strategy_results,
        strategiesCount: Object.keys(optimizationResult.strategy_results || {}).length,
        bestStrategy: optimizationResult.auto_selected_best?.name
      });

      // Skicka ytterligare event för att säkerställa att Visualization får data
      window.dispatchEvent(new CustomEvent('updateMapData', { 
        detail: { 
          result: optimizationResult,
          selectedStrategy: optimizationResult.auto_selected_best?.name,
          timestamp: new Date().toISOString()
        } 
      }));

      // Navigera till visualization-sidan med en liten fördröjning
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('navigate', { detail: 'visualization' }));
      }, 100);
    }
  };

  // Applicera den valda strategin
  const handleApplyStrategy = async () => {
    if (!optimizationResult?.auto_selected_best) {
      setError('Ingen strategi vald att applicera.');
      return;
    }

    try {
      // Här kan du lägga till API-anrop för att faktiskt applicera strategin
      // await api.applyStrategy(optimizationResult.auto_selected_best.name);
      
      alert(`Strategin "${optimizationResult.auto_selected_best.name}" skulle appliceras här. (Ej implementerat ännu)`);
    } catch (err) {
      console.error("Error applying strategy:", err);
      setError('Kunde inte applicera strategin.');
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Automatisk Optimering
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
        Systemet kommer automatiskt att testa alla tillgängliga strategier och välja den som placerar flest antal båtar.
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Kör Automatisk Optimering
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          Tillgängliga strategier: {strategies.map(s => s.name).join(', ') || 'Laddar...'}
        </Typography>
        
        {loading && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              {currentStrategy}
            </Typography>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
              {progress}% slutfört
            </Typography>
          </Box>
        )}
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleRunOptimization}
            disabled={loading || strategies.length === 0}
          >
            {loading ? <CircularProgress size={24} /> : 'Starta Automatisk Optimering'}
          </Button>
          
          {optimizationResult && (
            <>
              <Button
                variant="contained"
                color="success"
                onClick={handleViewOnMap}
                disabled={loading}
                sx={{ bgcolor: '#2E7D32', '&:hover': { bgcolor: '#1B5E20' } }}
              >
                🗺️ Visa på Karta
              </Button>
              
              <Button
                variant="outlined"
                color="secondary"
                onClick={handleApplyStrategy}
                disabled={loading}
              >
                Applicera Bästa Strategin
              </Button>
            </>
          )}
        </Box>
      </Paper>
      
      {optimizationResult && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Optimeringsresultat
          </Typography>
          
          {/* Visa den automatiskt valda bästa strategin */}
          {optimizationResult.auto_selected_best && (
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                <strong>🎯 Bästa Strategi (Automatiskt Vald):</strong> {optimizationResult.auto_selected_best.name}
              </Typography>
              <Typography variant="body2">
                <strong>Placerade båtar:</strong> {optimizationResult.auto_selected_best.evaluation.boats_placed} av {optimizationResult.auto_selected_best.evaluation.total_boats}
              </Typography>
              <Typography variant="body2">
                <strong>Placeringsgrad:</strong> {(optimizationResult.auto_selected_best.evaluation.placement_rate * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2">
                <strong>Utnyttjandegrad:</strong> {(optimizationResult.auto_selected_best.evaluation.utilization * 100).toFixed(1)}%
              </Typography>
            </Alert>
          )}
          
          {optimizationResult.gpt_analysis && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body1">
                {optimizationResult.gpt_analysis.recommendations && optimizationResult.gpt_analysis.recommendations.length > 0 ? 
                 optimizationResult.gpt_analysis.recommendations[0] : 
                 'Ingen specifik rekommendation tillgänglig.'}
              </Typography>
            </Box>
          )}
          
          <Typography variant="h6" gutterBottom>
            Detaljerad Jämförelse av Alla Strategier
          </Typography>
          
          <Grid container spacing={2}>
            {Object.entries(optimizationResult.evaluations || {})
              .sort(([,a], [,b]) => b.boats_placed - a.boats_placed) // Sortera efter antal placerade båtar
              .map(([strategyName, evaluation], index) => (
              <Grid item xs={12} md={6} lg={4} key={strategyName}>
                <Paper sx={{ 
                  p: 2, 
                  bgcolor: strategyName === optimizationResult.auto_selected_best?.name ? '#e8f5e8' : 'inherit',
                  border: strategyName === optimizationResult.auto_selected_best?.name ? '2px solid #4caf50' : '1px solid #e0e0e0',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 3
                  }
                }}>
                  {index === 0 && (
                    <Box sx={{ 
                      position: 'absolute', 
                      top: -10, 
                      right: 10, 
                      backgroundColor: '#4caf50', 
                      color: 'white', 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}>
                      BÄST
                    </Box>
                  )}
                  
                  <Typography variant="subtitle1" gutterBottom>
                    {strategyName}
                    {strategyName === optimizationResult.auto_selected_best?.name && ' ⭐'}
                  </Typography>
                  
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      <strong>Placerade båtar:</strong> {evaluation.boats_placed} / {evaluation.total_boats}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Placeringsgrad:</strong> {(evaluation.placement_rate * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">
                      <strong>Utnyttjandegrad:</strong> {(evaluation.utilization * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">
                      <strong>Poäng:</strong> {(evaluation.score * 100).toFixed(1)}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'info.main', color: 'info.contrastText', borderRadius: 1 }}>
            <Typography variant="body2">
              <strong>💡 Automatisk Optimering:</strong> Systemet testade {Object.keys(optimizationResult.evaluations || {}).length} strategier 
              och valde automatiskt den som placerar flest båtar. Strategin "{optimizationResult.auto_selected_best?.name}" 
              är optimal för att maximera antalet placerade båtar.
            </Typography>
          </Box>

          <Box sx={{ mt: 2, p: 2, bgcolor: 'success.light', borderRadius: 1, textAlign: 'center' }}>
            <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
              🗺️ Klicka på "Visa på Karta" för att se de faktiska båtplaceringarna!
            </Typography>
            <Typography variant="body2">
              Du kan sedan växla mellan olika strategier för att jämföra resultaten visuellt.
            </Typography>
          </Box>
        </Paper>
      )}
    </Container>
  );
}