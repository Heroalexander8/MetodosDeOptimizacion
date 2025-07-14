import pandas as pd
import numpy as np
import os
from scipy.optimize import minimize
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

class AggressivePortfolioOptimizer:
    def __init__(self):
        self.PRESUPUESTO = 1_000_000
        self.LAMBDA = 0.5  # Factor de aversión al riesgo
        self.MAX_SECTOR_WEIGHT = 0.30
        self.MIN_ASSETS = 5
        self.MAX_BETA = 1.2
        self.data = None
        self.optimal_portfolio = None
        
    def load_data(self, filename='Ronda1.xlsx'):
        """Carga los datos del archivo Excel desde el directorio actual"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, filename)
            
            if not os.path.exists(file_path):
                print(f"❌ Error: No se encontró el archivo {filename} en {current_dir}")
                return False
            
            self.data = pd.read_excel(file_path)
            print(f"✅ Datos cargados exitosamente: {len(self.data)} activos")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def aggressive_optimization(self):
        """Optimización agresiva para maximizar puntaje"""
        if self.data is None:
            print("❌ No hay datos cargados")
            return None
        
        print("\n🚀 INICIANDO OPTIMIZACIÓN AGRESIVA PARA GANAR EL PREMIO! 🏆")
        print("="*70)
        
        # Calcular múltiples métricas de eficiencia
        self.data['utility_score'] = self.data['retorno_esperado'] - self.LAMBDA * self.data['volatilidad']
        self.data['sharpe_ratio'] = self.data['retorno_esperado'] / self.data['volatilidad']
        self.data['return_per_dollar'] = self.data['retorno_esperado'] / self.data['precio_accion']
        self.data['efficiency_combo'] = (self.data['utility_score'] * 0.4 + 
                                        self.data['sharpe_ratio'] * 0.3 + 
                                        self.data['return_per_dollar'] * 0.3)
        
        best_portfolio = None
        best_score = -999999
        attempts = 0
        
        print("🔥 Probando múltiples estrategias...")
        
        # Estrategia 1: Top performers por sector
        portfolio1 = self._strategy_top_performers_by_sector()
        score1 = self._calculate_score(portfolio1) if portfolio1 else -999999
        print(f"📊 Estrategia 1 - Top por sector: Puntaje = {score1:.0f}")
        
        # Estrategia 2: Máximo retorno con restricciones
        portfolio2 = self._strategy_maximum_return()
        score2 = self._calculate_score(portfolio2) if portfolio2 else -999999
        print(f"📊 Estrategia 2 - Máximo retorno: Puntaje = {score2:.0f}")
        
        # Estrategia 3: Óptimo balanceado
        portfolio3 = self._strategy_balanced_optimal()
        score3 = self._calculate_score(portfolio3) if portfolio3 else -999999
        print(f"📊 Estrategia 3 - Balanceado óptimo: Puntaje = {score3:.0f}")
        
        # Estrategia 4: High-risk high-reward
        portfolio4 = self._strategy_high_risk_reward()
        score4 = self._calculate_score(portfolio4) if portfolio4 else -999999
        print(f"📊 Estrategia 4 - Alto riesgo/retorno: Puntaje = {score4:.0f}")
        
        # Seleccionar la mejor estrategia
        strategies = [
            (portfolio1, score1, "Top por sector"),
            (portfolio2, score2, "Máximo retorno"),
            (portfolio3, score3, "Balanceado óptimo"),
            (portfolio4, score4, "Alto riesgo/retorno")
        ]
        
        best_portfolio, best_score, best_strategy = max(strategies, key=lambda x: x[1])
        
        print(f"\n🏆 MEJOR ESTRATEGIA: {best_strategy}")
        print(f"🎯 PUNTAJE MÁXIMO ALCANZADO: {best_score:.0f}")
        
        self.optimal_portfolio = best_portfolio
        return best_portfolio
    
    def _strategy_top_performers_by_sector(self):
        """Estrategia: Mejores performers por cada sector"""
        portfolio = []
        total_investment = 0
        sector_investments = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        # Obtener top 3-4 activos por sector ordenados por utility_score
        for sector in [1, 2, 3, 4, 5]:
            sector_data = self.data[self.data['sector'] == sector].sort_values('utility_score', ascending=False)
            sector_budget = self.PRESUPUESTO * 0.28  # Usar casi el máximo permitido (30%)
            sector_investment = 0
            
            for _, asset in sector_data.iterrows():
                if sector_investment >= sector_budget:
                    break
                
                # Calcular inversión óptima (más agresiva)
                max_possible_investment = min(
                    sector_budget - sector_investment,
                    self.PRESUPUESTO - total_investment
                )
                
                if max_possible_investment < asset['min_inversion']:
                    continue
                
                # Invertir agresivamente - usar múltiplos de la inversión mínima
                target_investment = min(max_possible_investment, asset['min_inversion'] * 3)
                shares = int(target_investment / asset['precio_accion'])
                actual_investment = shares * asset['precio_accion']
                
                if actual_investment >= asset['min_inversion'] and actual_investment <= max_possible_investment:
                    portfolio.append({
                        'activo_id': asset['activo_id'],
                        'shares': shares,
                        'investment': actual_investment,
                        'retorno_esperado': asset['retorno_esperado'],
                        'volatilidad': asset['volatilidad'],
                        'beta': asset['beta'],
                        'sector': asset['sector'],
                        'precio_accion': asset['precio_accion'],
                        'min_inversion': asset['min_inversion'],
                        'liquidez_score': asset['liquidez_score']
                    })
                    
                    total_investment += actual_investment
                    sector_investment += actual_investment
                    sector_investments[sector] += actual_investment
        
        return portfolio if len(portfolio) >= self.MIN_ASSETS else None
    
    def _strategy_maximum_return(self):
        """Estrategia: Maximizar retorno respetando restricciones"""
        # Ordenar por retorno esperado
        sorted_data = self.data.sort_values('retorno_esperado', ascending=False)
        
        portfolio = []
        total_investment = 0
        sector_investments = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for _, asset in sorted_data.iterrows():
            if total_investment >= self.PRESUPUESTO * 0.95:
                break
            
            # Verificar restricción de sector
            max_sector_investment = self.PRESUPUESTO * self.MAX_SECTOR_WEIGHT
            available_sector_budget = max_sector_investment - sector_investments[asset['sector']]
            
            if available_sector_budget < asset['min_inversion']:
                continue
            
            # Calcular inversión
            max_investment = min(
                available_sector_budget,
                self.PRESUPUESTO - total_investment,
                asset['min_inversion'] * 5  # Más agresivo
            )
            
            shares = int(max_investment / asset['precio_accion'])
            actual_investment = shares * asset['precio_accion']
            
            if actual_investment >= asset['min_inversion']:
                portfolio.append({
                    'activo_id': asset['activo_id'],
                    'shares': shares,
                    'investment': actual_investment,
                    'retorno_esperado': asset['retorno_esperado'],
                    'volatilidad': asset['volatilidad'],
                    'beta': asset['beta'],
                    'sector': asset['sector'],
                    'precio_accion': asset['precio_accion'],
                    'min_inversion': asset['min_inversion'],
                    'liquidez_score': asset['liquidez_score']
                })
                
                total_investment += actual_investment
                sector_investments[asset['sector']] += actual_investment
        
        return portfolio if len(portfolio) >= self.MIN_ASSETS else None
    
    def _strategy_balanced_optimal(self):
        """Estrategia: Balanceado pero agresivo"""
        portfolio = []
        total_investment = 0
        sector_investments = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        # Ordenar por efficiency_combo
        sorted_data = self.data.sort_values('efficiency_combo', ascending=False)
        
        target_per_sector = self.PRESUPUESTO * 0.20  # 20% por sector
        
        for _, asset in sorted_data.iterrows():
            if len(portfolio) >= 15:  # Limitar número de activos
                break
            
            sector = asset['sector']
            available_budget = min(
                target_per_sector - sector_investments[sector],
                self.PRESUPUESTO - total_investment
            )
            
            if available_budget < asset['min_inversion']:
                continue
            
            # Inversión agresiva
            target_investment = min(available_budget, asset['min_inversion'] * 4)
            shares = int(target_investment / asset['precio_accion'])
            actual_investment = shares * asset['precio_accion']
            
            if actual_investment >= asset['min_inversion']:
                portfolio.append({
                    'activo_id': asset['activo_id'],
                    'shares': shares,
                    'investment': actual_investment,
                    'retorno_esperado': asset['retorno_esperado'],
                    'volatilidad': asset['volatilidad'],
                    'beta': asset['beta'],
                    'sector': asset['sector'],
                    'precio_accion': asset['precio_accion'],
                    'min_inversion': asset['min_inversion'],
                    'liquidez_score': asset['liquidez_score']
                })
                
                total_investment += actual_investment
                sector_investments[sector] += actual_investment
        
        return portfolio if len(portfolio) >= self.MIN_ASSETS else None
    
    def _strategy_high_risk_reward(self):
        """Estrategia: Alto riesgo, alto retorno"""
        # Filtrar activos con retorno > 12% y volatilidad < 25%
        high_performers = self.data[
            (self.data['retorno_esperado'] > 12) & 
            (self.data['volatilidad'] < 25) &
            (self.data['beta'] <= 1.4)
        ].sort_values('retorno_esperado', ascending=False)
        
        if len(high_performers) < self.MIN_ASSETS:
            # Relajar criterios si no hay suficientes
            high_performers = self.data[
                self.data['retorno_esperado'] > 10
            ].sort_values('retorno_esperado', ascending=False)
        
        portfolio = []
        total_investment = 0
        sector_investments = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for _, asset in high_performers.iterrows():
            if total_investment >= self.PRESUPUESTO * 0.90:
                break
            
            max_sector_investment = self.PRESUPUESTO * self.MAX_SECTOR_WEIGHT
            available_sector_budget = max_sector_investment - sector_investments[asset['sector']]
            
            if available_sector_budget < asset['min_inversion']:
                continue
            
            # Inversión muy agresiva
            max_investment = min(
                available_sector_budget,
                self.PRESUPUESTO - total_investment,
                asset['min_inversion'] * 8  # Muy agresivo
            )
            
            shares = int(max_investment / asset['precio_accion'])
            actual_investment = shares * asset['precio_accion']
            
            if actual_investment >= asset['min_inversion']:
                portfolio.append({
                    'activo_id': asset['activo_id'],
                    'shares': shares,
                    'investment': actual_investment,
                    'retorno_esperado': asset['retorno_esperado'],
                    'volatilidad': asset['volatilidad'],
                    'beta': asset['beta'],
                    'sector': asset['sector'],
                    'precio_accion': asset['precio_accion'],
                    'min_inversion': asset['min_inversion'],
                    'liquidez_score': asset['liquidez_score']
                })
                
                total_investment += actual_investment
                sector_investments[asset['sector']] += actual_investment
        
        return portfolio if len(portfolio) >= self.MIN_ASSETS else None
    
    def _calculate_score(self, portfolio):
        """Calcula el puntaje de un portafolio"""
        if not portfolio:
            return -999999
        
        portfolio_df = pd.DataFrame(portfolio)
        total_investment = portfolio_df['investment'].sum()
        
        if total_investment == 0:
            return -999999
        
        # Calcular pesos
        portfolio_df['weight'] = portfolio_df['investment'] / total_investment
        
        # Métricas del portafolio
        portfolio_return = (portfolio_df['retorno_esperado'] * portfolio_df['weight']).sum()
        portfolio_volatility = np.sqrt(((portfolio_df['volatilidad'] * portfolio_df['weight']) ** 2).sum())
        portfolio_beta = (portfolio_df['beta'] * portfolio_df['weight']).sum()
        
        # Verificar restricciones
        sector_weights = {}
        for sector in [1, 2, 3, 4, 5]:
            sector_investment = portfolio_df[portfolio_df['sector'] == sector]['investment'].sum()
            sector_weights[sector] = sector_investment / total_investment
        
        constraints_met = {
            'budget': total_investment <= self.PRESUPUESTO,
            'diversification': len(portfolio) >= self.MIN_ASSETS,
            'beta_limit': portfolio_beta <= self.MAX_BETA,
            'sector_limits': all(weight <= self.MAX_SECTOR_WEIGHT for weight in sector_weights.values())
        }
        
        # Factor de restricciones
        Fr = 1.0 if all(constraints_met.values()) else 0.8
        
        # Utilidad y puntaje
        utility = portfolio_return - self.LAMBDA * portfolio_volatility
        score = 1000 * utility * Fr
        
        return score
    
    def calculate_detailed_metrics(self):
        """Calcula métricas detalladas del portafolio optimizado"""
        if not self.optimal_portfolio:
            return None
        
        portfolio_df = pd.DataFrame(self.optimal_portfolio)
        total_investment = portfolio_df['investment'].sum()
        
        # Calcular pesos
        portfolio_df['weight'] = portfolio_df['investment'] / total_investment
        
        # Métricas del portafolio
        portfolio_return = (portfolio_df['retorno_esperado'] * portfolio_df['weight']).sum()
        portfolio_volatility = np.sqrt(((portfolio_df['volatilidad'] * portfolio_df['weight']) ** 2).sum())
        portfolio_beta = (portfolio_df['beta'] * portfolio_df['weight']).sum()
        
        # Distribución por sectores
        sector_weights = {}
        sector_investments = {}
        for sector in [1, 2, 3, 4, 5]:
            sector_data = portfolio_df[portfolio_df['sector'] == sector]
            sector_investment = sector_data['investment'].sum()
            sector_investments[sector] = sector_investment
            sector_weights[sector] = sector_investment / total_investment if total_investment > 0 else 0
        
        # Verificar restricciones
        constraints = {
            'budget': total_investment <= self.PRESUPUESTO,
            'diversification': len(self.optimal_portfolio) >= self.MIN_ASSETS,
            'beta_limit': portfolio_beta <= self.MAX_BETA,
            'sector_limits': all(weight <= self.MAX_SECTOR_WEIGHT for weight in sector_weights.values())
        }
        
        Fr = 1.0 if all(constraints.values()) else 0.8
        utility = portfolio_return - self.LAMBDA * portfolio_volatility
        score = 1000 * utility * Fr
        
        return {
            'portfolio_df': portfolio_df,
            'portfolio_return': portfolio_return,
            'portfolio_volatility': portfolio_volatility,
            'portfolio_beta': portfolio_beta,
            'utility': utility,
            'score': score,
            'constraints': constraints,
            'Fr': Fr,
            'total_investment': total_investment,
            'available_budget': self.PRESUPUESTO - total_investment,
            'sector_weights': sector_weights,
            'sector_investments': sector_investments
        }
    
    def print_champion_results(self):
        """Imprime resultados optimizados para ganar"""
        metrics = self.calculate_detailed_metrics()
        if not metrics:
            return
        
        print("\n" + "🏆" * 25)
        print("🚀 PORTAFOLIO OPTIMIZADO PARA GANAR EL PREMIO 🚀")
        print("🏆" * 25)
        
        # Métricas principales con colores
        print(f"\n🎯 PUNTAJE FINAL: {metrics['score']:.0f}")
        print(f"📈 RETORNO ESPERADO: {metrics['portfolio_return']:.2f}%")
        print(f"📊 VOLATILIDAD: {metrics['portfolio_volatility']:.2f}%")
        print(f"⚖️  BETA: {metrics['portfolio_beta']:.2f}")
        print(f"💎 UTILIDAD: {metrics['utility']:.2f}")
        
        # Utilización del presupuesto
        usage_pct = (metrics['total_investment'] / self.PRESUPUESTO) * 100
        print(f"\n💰 UTILIZACIÓN DEL PRESUPUESTO:")
        print(f"   💵 Invertido: S/.{metrics['total_investment']:,.0f} ({usage_pct:.1f}%)")
        print(f"   🏦 Disponible: S/.{metrics['available_budget']:,.0f}")
        
        # Estado de restricciones
        print(f"\n✅ VERIFICACIÓN DE RESTRICCIONES:")
        icons = {"True": "✅", "False": "❌"}
        for constraint, status in metrics['constraints'].items():
            icon = icons[str(status)]
            if constraint == 'sector_limits':
                print(f"   {icon} Límites sectoriales (max 30% por sector)")
            elif constraint == 'beta_limit':
                print(f"   {icon} Beta ≤ 1.2 (actual: {metrics['portfolio_beta']:.2f})")
            elif constraint == 'diversification':
                print(f"   {icon} Mínimo 5 activos ({len(self.optimal_portfolio)} seleccionados)")
            else:
                print(f"   {icon} {constraint}")
        
        # Distribución por sectores
        sectores = {1: 'Tech', 2: 'Salud', 3: 'Energía', 4: 'Financiero', 5: 'Consumo'}
        print(f"\n🏭 DISTRIBUCIÓN POR SECTORES:")
        for sector, weight in metrics['sector_weights'].items():
            if weight > 0:
                investment = metrics['sector_investments'][sector]
                status = "✅" if weight <= self.MAX_SECTOR_WEIGHT else "❌"
                print(f"   {status} {sectores[sector]}: {weight*100:.1f}% (S/.{investment:,.0f})")
        
        # Portafolio detallado
        print(f"\n📈 PORTAFOLIO GANADOR ({len(self.optimal_portfolio)} activos):")
        print("-" * 110)
        print(f"{'Activo':<8} {'Acciones':<10} {'Inversión':<15} {'Peso':<8} {'Retorno':<8} {'Volat.':<8} {'Beta':<6} {'Sector':<12}")
        print("-" * 110)
        
        portfolio_df = metrics['portfolio_df']
        for _, asset in portfolio_df.iterrows():
            sector_name = sectores[asset['sector']]
            print(f"{asset['activo_id']:<8} {asset['shares']:<10,} S/.{asset['investment']:<12,.0f} "
                  f"{asset['weight']*100:<6.1f}% {asset['retorno_esperado']:<6.1f}% "
                  f"{asset['volatilidad']:<6.1f}% {asset['beta']:<6.2f} {sector_name:<12}")
        
        print("-" * 110)
        print(f"{'TOTAL':<19} S/.{metrics['total_investment']:<12,.0f} "
              f"{'100.0%':<6} {metrics['portfolio_return']:<6.1f}% "
              f"{metrics['portfolio_volatility']:<6.1f}% {metrics['portfolio_beta']:<6.2f}")
        
        # Mensaje motivacional
        print(f"\n🚀 PROBABILIDAD DE GANAR: {'🔥 ALTA 🔥' if metrics['score'] > 3000 else '⚡ BUENA ⚡' if metrics['score'] > 2000 else '📈 MODERADA'}")

def main():
    """Función principal para ganar el premio"""
    print("🏆" * 20)
    print("🚀 OPTIMIZADOR AGRESIVO - MODO CAMPEON 🚀")
    print("🏆" * 20)
    
    optimizer = AggressivePortfolioOptimizer()
    
    if not optimizer.load_data():
        return
    
    # Optimización agresiva
    portfolio = optimizer.aggressive_optimization()
    
    if portfolio:
        optimizer.print_champion_results()
        print(f"\n🎉 ¡PORTAFOLIO LISTO PARA GANAR EL PREMIO! 🎉")
    else:
        print("❌ Error en la optimización")

if __name__ == "__main__":
    main()