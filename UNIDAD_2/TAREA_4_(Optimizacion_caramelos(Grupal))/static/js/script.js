// --- Constantes del Juego ---
const CANDY_TYPES = {
    LEMON: { name: 'Limón', emoji: '🍋' },
    PEAR: { name: 'Pera', emoji: '🍐' },
    EGG: { name: 'Huevo', emoji: '🥚' }
};
const ALL_CANDIES = [CANDY_TYPES.LEMON, CANDY_TYPES.PEAR, CANDY_TYPES.EGG];
const MAX_PLAYERS = 28; // Ajustado a 28 para ser divisible por GROUP_SIZE (4)
const PLAYER_INITIAL_CANDIES = 2; // Cada jugador comienza con 2 dulces
const GROUP_SIZE = 4; // Grupos de 4 integrantes
const GAME_TIME_LIMIT_SECONDS = 5 * 60; // ¡Configurado a 5 minutos (300 segundos)!

// Objetivo de dulces para cada grupo: 2 de cada tipo
const GROUP_OBJECTIVE_CANDIES = {
    [CANDY_TYPES.LEMON.name]: 2,
    [CANDY_TYPES.PEAR.name]: 2,
    [CANDY_TYPES.EGG.name]: 2
};

// --- Variables de Estado del Juego ---
let players = [];
let groups = [];
let gameTimerInterval = null; // Para el temporizador de cuenta regresiva
let gameExchangeInterval = null; // Para el bucle de intercambios
let timeLeft = GAME_TIME_LIMIT_SECONDS;
let gameStarted = false;
let globalExchangeLog = []; // Log de todos los intercambios realizados

// --- Referencias a Elementos del DOM ---
const generatePlayersBtn = document.getElementById('generatePlayersBtn');
const addPlayerBtn = document.getElementById('addPlayerBtn');
const playerNameInput = document.getElementById('playerNameInput');
const playerList = document.getElementById('playerList');
const playerCountSpan = document.getElementById('playerCount');
const startGameBtn = document.getElementById('startGameBtn');
const stopGameBtn = document.getElementById('stopGameBtn');
const resetGameBtn = document.getElementById('resetGameBtn');
const gameTimerDisplay = document.getElementById('gameTimer');
const groupsContainer = document.getElementById('groupsContainer');
const resultsContainer = document.getElementById('resultsContainer');
const globalExchangeLogDisplay = document.getElementById('globalExchangeLog');

// --- Funciones de Utilidad ---

/**
 * Genera un ID único simple para jugadores/grupos.
 * @returns {string} Un ID único.
 */
function generateUniqueId() {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

/**
 * Obtiene un dulce aleatorio.
 * @returns {object} Un objeto de tipo de dulce (LEMON, PEAR, EGG).
 */
function getRandomCandy() {
    const randomIndex = Math.floor(Math.random() * ALL_CANDIES.length);
    return ALL_CANDIES[randomIndex];
}

/**
 * Mezcla aleatoriamente un array (algoritmo de Fisher-Yates).
 * @param {Array} array El array a mezclar.
 * @returns {Array} El array mezclado.
 */
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

/**
 * Cuenta la cantidad de cada tipo de dulce en una colección.
 * @param {Array<object>} candies Array de objetos de dulces.
 * @returns {object} Objeto con el conteo de cada dulce.
 */
function countCandies(candies) {
    const counts = {};
    ALL_CANDIES.forEach(type => {
        counts[type.name] = 0;
    });
    candies.forEach(candy => {
        counts[candy.name]++;
    });
    return counts;
}

/**
 * Verifica si un grupo ha logrado el objetivo de dulces (2 de cada tipo).
 * @param {Array<object>} groupMembers Array de objetos de jugador que pertenecen al grupo.
 * @returns {boolean} True si el grupo ha logrado el objetivo, false en caso contrario.
 */
function checkGroupObjective(groupMembers) {
    const allGroupCandies = [];
    groupMembers.forEach(member => {
        allGroupCandies.push(...member.candies);
    });

    const currentCandyCounts = countCandies(allGroupCandies);

    for (const candyName in GROUP_OBJECTIVE_CANDIES) {
        if (currentCandyCounts[candyName] < GROUP_OBJECTIVE_CANDIES[candyName]) {
            return false; // Si falta algún dulce para el objetivo, el objetivo no está logrado
        }
    }
    return true; // Si todos los dulces cumplen o superan el objetivo, está logrado
}

/**
 * Calcula la "puntuación de déficit" de un grupo. Menor puntuación es mejor.
 * @param {Array<object>} groupMembers Array de objetos de jugador.
 * @returns {number} Suma de los dulces que faltan para alcanzar el objetivo.
 */
function calculateGroupDeficitScore(groupMembers) {
    const currentCounts = countCandies(groupMembers.flatMap(m => m.candies));
    let deficit = 0;
    for (const candyName in GROUP_OBJECTIVE_CANDIES) {
        deficit += Math.max(0, GROUP_OBJECTIVE_CANDIES[candyName] - currentCounts[candyName]);
    }
    return deficit;
}


// --- Gestión de Jugadores ---

/**
 * Genera un jugador con un nombre y dulces específicos.
 * @param {string} name Nombre del jugador.
 * @param {object[]} candies Dulces iniciales (objetos de dulce).
 * @returns {object} Objeto jugador.
 */
function createPlayer(name, candies) {
    return {
        id: generateUniqueId(),
        name: name,
        candies: candies,
        isSurvivor: false,
        exchangeLog: [] // Log de intercambios personales (no usado en esta iteración para simplificar)
    };
}

/**
 * Renderiza la lista de jugadores en el DOM.
 */
function renderPlayers() {
    playerList.innerHTML = '';
    players.forEach(player => {
        const li = document.createElement('li');
        li.className = 'player-item';
        li.innerHTML = `
            <span>${player.name}</span>
            <div class="candies">
                ${player.candies.map(candy => `<span class="candy-icon candy-${candy.name.toLowerCase()}">${candy.emoji}</span>`).join('')}
            </div>
        `;
        playerList.appendChild(li);
    });
    playerCountSpan.textContent = players.length;
    updateGameControls();
}

/**
 * Genera automáticamente un número predefinido de jugadores con una distribución de dulces que garantiza el éxito.
 * La distribución se realiza por grupo para asegurar que cada grupo tenga los dulces necesarios.
 */
function generateAutomaticPlayers() {
    players = []; // Limpiar jugadores existentes
    
    // Asegurarse de que MAX_PLAYERS sea divisible por GROUP_SIZE
    const actualMaxPlayers = Math.floor(MAX_PLAYERS / GROUP_SIZE) * GROUP_SIZE;
    
    const numberOfGroups = actualMaxPlayers / GROUP_SIZE;
    const totalCandiesPerGroup = GROUP_SIZE * PLAYER_INITIAL_CANDIES; // 4 * 2 = 8 dulces por grupo
    const totalObjectiveCandiesPerGroup = Object.values(GROUP_OBJECTIVE_CANDIES).reduce((sum, count) => sum + count, 0); // 2+2+2 = 6 dulces objetivo

    for (let g = 0; g < numberOfGroups; g++) {
        let groupCandyPool = [];

        // 1. Añadir los dulces del objetivo para este grupo (6 dulces)
        for (const candyName in GROUP_OBJECTIVE_CANDIES) {
            for (let k = 0; k < GROUP_OBJECTIVE_CANDIES[candyName]; k++) {
                groupCandyPool.push(ALL_CANDIES.find(c => c.name === candyName));
            }
        }

        // 2. Añadir los dulces "extra" para completar el total de dulces del grupo (2 dulces extra)
        const extraCandiesCount = totalCandiesPerGroup - totalObjectiveCandiesPerGroup;
        for (let i = 0; i < extraCandiesCount; i++) {
            // Distribuir los dulces extra de manera que faciliten el intercambio.
            // Para garantizar 100% de éxito, podemos añadir dulces que no sean "excedentes"
            // o simplemente aleatorios. Aquí, los hacemos aleatorios.
            groupCandyPool.push(getRandomCandy()); 
        }

        // 3. Mezclar los dulces de este grupo para distribuirlos entre sus miembros
        groupCandyPool = shuffleArray(groupCandyPool);

        // 4. Distribuir estos dulces entre los jugadores de este grupo
        for (let p = 0; p < GROUP_SIZE; p++) {
            const playerCandies = [];
            for (let c = 0; c < PLAYER_INITIAL_CANDIES; c++) {
                // Tomar dulces del pool del grupo y asignarlos al jugador
                playerCandies.push(groupCandyPool.pop()); // pop() para asegurar que cada dulce se usa una vez
            }
            players.push(createPlayer(`Jugador ${g * GROUP_SIZE + p + 1}`, playerCandies));
        }
    }

    renderPlayers();
    console.log(`${actualMaxPlayers} jugadores generados automáticamente con distribución de dulces optimizada para 100% de éxito.`);
}

/**
 * Agrega un jugador manualmente desde el input.
 */
function addPlayerManually() {
    const name = playerNameInput.value.trim();
    if (name) {
        // Para jugadores manuales, se les asignan dulces aleatorios como antes.
        const manualPlayerCandies = [];
        for (let i = 0; i < PLAYER_INITIAL_CANDIES; i++) {
            manualPlayerCandies.push(getRandomCandy());
        }
        players.push(createPlayer(name, manualPlayerCandies));
        playerNameInput.value = '';
        renderPlayers();
        console.log(`Jugador "${name}" agregado manualmente.`);
    } else {
        alert('Por favor, ingresa un nombre para el jugador.');
    }
}

// --- Gestión del Juego ---

/**
 * Actualiza el estado de los botones de control del juego.
 */
function updateGameControls() {
    startGameBtn.disabled = players.length < GROUP_SIZE || gameStarted;
    stopGameBtn.disabled = !gameStarted;
    resetGameBtn.disabled = false; // Siempre se puede reiniciar
}

/**
 * Inicia el temporizador del juego.
 */
function startTimer() {
    clearInterval(gameTimerInterval); // Limpiar cualquier intervalo previo
    gameTimerInterval = setInterval(() => {
        timeLeft--;
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        gameTimerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        if (timeLeft <= 0) {
            endGame('time_up');
        }
    }, 1000);
}

/**
 * Detiene el temporizador del juego.
 */
function functionstopTimer() {
    clearInterval(gameTimerInterval);
    gameTimerInterval = null;
}

/**
 * Inicia el juego: forma grupos, inicia temporizador y bucle de intercambios.
 */
function startGame() {
    if (players.length < GROUP_SIZE) {
        alert(`Necesitas al menos ${GROUP_SIZE} jugadores para formar un grupo.`);
        return;
    }
    
    gameStarted = true;
    timeLeft = GAME_TIME_LIMIT_SECONDS; // Reiniciar tiempo
    globalExchangeLog = []; // Limpiar log global al inicio de un nuevo juego
    resultsContainer.innerHTML = ''; // Limpiar resultados anteriores
    renderGlobalExchangeLog(); // Renderizar el log vacío

    formGroups(); // Formar grupos
    startTimer(); // Iniciar temporizador

    // Iniciar el bucle de intercambios
    // Los intercambios se realizarán cada 0.1 segundos (¡muy rápido!)
    gameExchangeInterval = setInterval(performExchangesInGroups, 100); // Ejecutar intercambios cada 0.1 segundos

    updateGameControls();
    console.log('Juego iniciado.');
    alert('¡Juego iniciado! ¡Que comiencen los intercambios!');
}

/**
 * Detiene el juego manualmente.
 */
function stopGame() {
    endGame('manual_stop');
}

/**
 * Reinicia el juego a su estado inicial.
 */
function resetGame() {
    endGame('reset'); // Esto detendrá los intervalos
    players = [];
    groups = [];
    globalExchangeLog = []; // Limpiar log global
    renderPlayers(); // Volver a generar jugadores automáticos por defecto
    renderGroups();
    renderGlobalExchangeLog(); // Renderizar log vacío
    resultsContainer.innerHTML = '';
    gameTimerDisplay.textContent = '05:00'; // Resetear a 05:00 visualmente
    console.log('Juego reiniciado.');
}

/**
 * Finaliza el juego y muestra los resultados.
 * @param {string} reason Razón por la que el juego terminó ('time_up', 'manual_stop', 'reset', 'all_objectives_achieved').
 */
function endGame(reason) {
    functionstopTimer(); // Detener el temporizador de cuenta regresiva
    clearInterval(gameExchangeInterval); // Detener el bucle de intercambios
    gameExchangeInterval = null;
    gameStarted = false;
    updateGameControls();
    console.log(`Juego terminado. Razón: ${reason}`);

    if (reason === 'time_up') {
        alert('¡Tiempo agotado! El juego ha terminado.');
    } else if (reason === 'manual_stop') {
        alert('Juego detenido manualmente.');
    } else if (reason === 'all_objectives_achieved') {
        alert('¡Todos los grupos han logrado sus objetivos! El juego ha terminado.');
    }
    
    // Mostrar resultados finales solo si no es un reinicio completo
    if (reason !== 'reset') {
        displayResults();
    }
}

// --- Formación y Renderizado de Grupos ---

/**
 * Forma grupos aleatorios de 3 jugadores.
 */
function formGroups() {
    groups = [];
    const shuffledPlayers = shuffleArray([...players]); // Mezclar jugadores para equipos justos

    for (let i = 0; i < shuffledPlayers.length; i += GROUP_SIZE) {
        const groupPlayers = shuffledPlayers.slice(i, i + GROUP_SIZE);
        if (groupPlayers.length === GROUP_SIZE) { // Solo formar grupos completos
            groups.push({
                id: generateUniqueId(),
                members: groupPlayers,
                objectiveAchieved: false, // Inicialmente no logrado
                survivor: null,
                exchangeLog: [] // Log de intercambios específico del grupo
            });
        }
    }
    renderGroups();
    console.log(`${groups.length} grupos formados.`);
}

/**
 * Renderiza los grupos en el DOM.
 */
function renderGroups() {
    groupsContainer.innerHTML = '';
    if (groups.length === 0) {
        groupsContainer.innerHTML = '<p class="info-message">No hay grupos formados aún. Genera jugadores e inicia el juego.</p>';
        return;
    }

    groups.forEach((group, index) => {
        const groupCard = document.createElement('div');
        groupCard.className = 'group-card';
        groupCard.innerHTML = `
            <h4>Grupo ${index + 1}</h4>
            ${group.members.map(member => `
                <div class="group-member">
                    <span>${member.name}</span>
                    <div class="candies">
                        ${member.candies.map(candy => `<span class="candy-icon candy-${candy.name.toLowerCase()}">${candy.emoji}</span>`).join('')}
                    </div>
                </div>
            `).join('')}
            <p class="group-status ${group.objectiveAchieved ? 'achieved' : ''}">Objetivo: ${group.objectiveAchieved ? '✅ Logrado' : '⏳ Pendiente'}</p>
            ${group.survivor ? `<p class="group-survivor">Sobreviviente: <strong>${group.survivor.name}</strong> 🍭</p>` : ''}
        `;
        groupsContainer.appendChild(groupCard);
    });
}

// --- Lógica de Intercambios (Optimización Heurística) ---

/**
 * Determina el "sobreviviente" de un grupo que ha logrado el objetivo.
 * El sobreviviente es el jugador con la mano más "diversa" (más tipos de dulces únicos).
 * Si hay empate, se elige aleatoriamente.
 * @param {object} group El objeto del grupo.
 * @returns {object} El objeto del jugador sobreviviente.
 */
function determineSurvivor(group) {
    let bestSurvivor = null;
    let maxUniqueCandies = -1;

    // Shuffle members to ensure fair chance if multiple players have same diversity
    const shuffledMembers = shuffleArray([...group.members]); 

    shuffledMembers.forEach(member => {
        const uniqueCandiesInHand = new Set(member.candies.map(c => c.name)).size;
        if (uniqueCandiesInHand > maxUniqueCandies) {
            maxUniqueCandies = uniqueCandiesInHand;
            bestSurvivor = member;
        }
        // No need for else if (uniqueCandiesInHand === maxUniqueCandies) and random pick
        // because we shuffled. The first one found with maxUniqueCandies is good enough.
    });
    return bestSurvivor;
}


/**
 * Realiza una ronda de intercambios en todos los grupos.
 * Implementa una estrategia de intercambio codiciosa (greedy heuristic).
 */
function performExchangesInGroups() {
    if (!gameStarted) return;

    let anyGroupMadeProgress = false; // Para saber si se hizo algún intercambio en esta ronda

    groups.forEach(group => {
        if (group.objectiveAchieved) return; // Saltar grupos que ya lograron el objetivo

        const initialDeficit = calculateGroupDeficitScore(group.members);
        let currentDeficit = initialDeficit;
        let exchangeMadeInGroup = false;

        // Mezclar miembros para dar oportunidades equitativas de intercambio
        const shuffledMembers = shuffleArray([...group.members]);

        // Iterar a través de cada par de jugadores en el grupo para intentar intercambios
        for (let i = 0; i < shuffledMembers.length; i++) {
            const player1 = shuffledMembers[i];
            for (let j = 0; j < shuffledMembers.length; j++) {
                if (i === j) continue; // No intercambiar consigo mismo
                const player2 = shuffledMembers[j];

                // Intentar intercambiar un dulce de player1 por un dulce de player2
                for (let k = 0; k < player1.candies.length; k++) {
                    const candy1 = player1.candies[k]; // Dulce que P1 podría dar
                    for (let l = 0; l < player2.candies.length; l++) {
                        const candy2 = player2.candies[l]; // Dulce que P2 podría dar

                        // Simular el intercambio para ver si mejora el déficit del grupo
                        const simulatedP1Candies = [...player1.candies];
                        simulatedP1Candies[k] = candy2; // P1 recibe candy2

                        const simulatedP2Candies = [...player2.candies];
                        simulatedP2Candies[l] = candy1; // P2 recibe candy1

                        const simulatedMembers = group.members.map(member => {
                            if (member.id === player1.id) return { ...player1, candies: simulatedP1Candies };
                            if (member.id === player2.id) return { ...player2, candies: simulatedP2Candies };
                            return member;
                        });

                        const newDeficit = calculateGroupDeficitScore(simulatedMembers);

                        if (newDeficit < currentDeficit) {
                            // ¡Intercambio beneficioso encontrado!
                            // Realizar el intercambio real
                            player1.candies[k] = candy2;
                            player2.candies[l] = candy1;
                            
                            const logMessage = `Grupo ${groups.indexOf(group) + 1}: ${player1.name} intercambió ${candy1.emoji} por ${candy2.emoji} de ${player2.name}.`;
                            group.exchangeLog.push(logMessage);
                            globalExchangeLog.push(logMessage);
                            console.log(logMessage);

                            exchangeMadeInGroup = true;
                            anyGroupMadeProgress = true;
                            currentDeficit = newDeficit; // Actualizar el déficit para futuros intercambios en este grupo

                            // Re-renderizar los grupos inmediatamente después de un intercambio
                            renderGroups();
                            renderGlobalExchangeLog();

                            // Verificar si el objetivo del grupo se ha logrado después de este intercambio
                            if (checkGroupObjective(group.members)) {
                                group.objectiveAchieved = true;
                                group.survivor = determineSurvivor(group); // Asignar sobreviviente
                                const survivorMessage = `¡Grupo ${groups.indexOf(group) + 1} logró el objetivo! Sobreviviente: ${group.survivor.name} 🍭`;
                                group.exchangeLog.push(survivorMessage);
                                globalExchangeLog.push(survivorMessage);
                                console.log(survivorMessage);
                                renderGroups(); // Actualizar el estado del grupo
                                displayResults(); // Actualizar resultados
                                return; // Salir de los bucles de este grupo, ya ha terminado
                            }
                            // Si se hizo un intercambio, podemos detenernos y dejar que la próxima ronda lo reevalúe
                            // Esto evita que un solo grupo monopolice los intercambios en una ronda
                            return; 
                        }
                    }
                }
            }
        }
    });

    // Si ningún grupo hizo progreso y el tiempo sigue corriendo, el juego podría estancarse.
    // Esto es más para depuración o para una lógica de juego más avanzada.
    // if (!anyGroupMadeProgress && gameStarted && timeLeft > 0) {
    //     console.log("Ningún grupo hizo progreso en esta ronda. El juego podría estar estancado o ya no hay intercambios beneficiosos.");
    // }

    // Verificar si todos los grupos han logrado el objetivo para terminar el juego antes de tiempo
    const allGroupsAchieved = groups.length > 0 && groups.every(group => group.objectiveAchieved);
    if (allGroupsAchieved) {
        endGame('all_objectives_achieved');
    }
}

/**
 * Renderiza el log de intercambios global.
 */
function renderGlobalExchangeLog() {
    globalExchangeLogDisplay.innerHTML = '';
    if (globalExchangeLog.length === 0) {
        globalExchangeLogDisplay.innerHTML = '<p class="info-message">Los intercambios aparecerán aquí una vez que el juego comience.</p>';
    } else {
        globalExchangeLog.forEach(log => {
            const p = document.createElement('p');
            p.textContent = log;
            globalExchangeLogDisplay.appendChild(p);
        });
        // Scroll al final para ver los últimos logs
        globalExchangeLogDisplay.scrollTop = globalExchangeLogDisplay.scrollHeight;
    }
}


// --- Resultados ---

/**
 * Muestra los resultados finales del juego.
 */
function displayResults() {
    resultsContainer.innerHTML = '<h3>Análisis de Resultados</h3>';
    let successfulGroups = 0;
    const lollipopWinners = [];

    if (groups.length === 0) {
        resultsContainer.innerHTML += '<p class="info-message">No se formaron grupos o el juego no se inició.</p>';
        return;
    }

    groups.forEach((group, index) => {
        const groupResult = document.createElement('div');
        groupResult.className = 'card group-result-card'; // Reutilizar estilo de tarjeta
        groupResult.innerHTML = `
            <h4>Resultados del Grupo ${index + 1}</h4>
            <p>Estado: ${group.objectiveAchieved ? '✅ Objetivo Logrado' : '❌ Objetivo No Logrado'}</p>
            ${group.survivor ? `<p>Sobreviviente: <strong>${group.survivor.name}</strong> (Ganador de Chupetín 🍭)</p>` : '<p>No hubo sobreviviente en este grupo.</p>'}
            <h5>Miembros Finales:</h5>
            <ul>
                ${group.members.map(member => `<li>${member.name} - Dulces: ${member.candies.map(c => c.emoji).join('')}</li>`).join('')}
            </ul>
            <h5>Log de Intercambios del Grupo:</h5>
            ${group.exchangeLog.length > 0 ? `
                <ul class="exchange-log-list">
                    ${group.exchangeLog.map(log => `<li>${log}</li>`).join('')}
                </ul>
            ` : '<p>No hubo intercambios registrados en este grupo.</p>'}
        `;
        resultsContainer.appendChild(groupResult);

        if (group.objectiveAchieved) {
            successfulGroups++;
            if (group.survivor) {
                lollipopWinners.push(group.survivor);
            }
        }
    });

    const successRate = (successfulGroups / groups.length) * 100;
    resultsContainer.innerHTML += `
        <div class="card final-summary-card">
            <h3>Resumen Final del Juego</h3>
            <p>Grupos Totales: <strong>${groups.length}</strong></p>
            <p>Grupos con Objetivo Logrado: <strong>${successfulGroups}</strong></p>
            <p>Tasa de Éxito: <strong>${successRate.toFixed(2)}%</strong></p>
            ${lollipopWinners.length > 0 ? `
                <h4>¡Ganadores de Chupetines! 🥳</h4>
                <ul>
                    ${lollipopWinners.map(winner => `<li>${winner.name} 🍭</li>`).join('')}
                </ul>
            ` : '<p>No hubo ganadores de chupetines en esta ronda.</p>'}
        </div>
    `;
}


// --- Inicialización y Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    generatePlayersBtn.addEventListener('click', generateAutomaticPlayers);
    addPlayerBtn.addEventListener('click', addPlayerManually);
    startGameBtn.addEventListener('click', startGame);
    stopGameBtn.addEventListener('click', stopGame);
    resetGameBtn.addEventListener('click', resetGame);

    // Inicializar con jugadores automáticos al cargar la página
    generateAutomaticPlayers();
    renderGroups(); // Renderizar grupos vacíos o mensaje inicial
    renderGlobalExchangeLog(); // Inicializar el log global
    updateGameControls(); // Asegurar el estado inicial de los botones
});
