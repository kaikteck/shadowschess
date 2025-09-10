// Chess piece symbols
const PIECES = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
};

// Initial chess board position
const INITIAL_POSITION = {
    'a8': 'bR', 'b8': 'bN', 'c8': 'bB', 'd8': 'bQ', 'e8': 'bK', 'f8': 'bB', 'g8': 'bN', 'h8': 'bR',
    'a7': 'bP', 'b7': 'bP', 'c7': 'bP', 'd7': 'bP', 'e7': 'bP', 'f7': 'bP', 'g7': 'bP', 'h7': 'bP',
    'a2': 'wP', 'b2': 'wP', 'c2': 'wP', 'd2': 'wP', 'e2': 'wP', 'f2': 'wP', 'g2': 'wP', 'h2': 'wP',
    'a1': 'wR', 'b1': 'wN', 'c1': 'wB', 'd1': 'wQ', 'e1': 'wK', 'f1': 'wB', 'g1': 'wN', 'h1': 'wR'
};

let currentBoard = {...INITIAL_POSITION};
let selectedSquare = null;
let draggedPiece = null;

function initializeChessBoard() {
    const boardElement = document.getElementById('practice-board');
    if (!boardElement) return;
    
    // Create board squares
    for (let rank = 8; rank >= 1; rank--) {
        for (let file = 0; file < 8; file++) {
            const fileChar = String.fromCharCode(97 + file); // a-h
            const square = fileChar + rank;
            
            const squareElement = document.createElement('div');
            squareElement.className = `chess-square ${(rank + file) % 2 === 0 ? 'dark' : 'light'}`;
            squareElement.dataset.square = square;
            
            // Add coordinate labels
            if (file === 0) {
                const rankLabel = document.createElement('div');
                rankLabel.className = 'rank-label';
                rankLabel.textContent = rank;
                rankLabel.style.position = 'absolute';
                rankLabel.style.top = '2px';
                rankLabel.style.left = '2px';
                rankLabel.style.fontSize = '10px';
                rankLabel.style.fontWeight = 'bold';
                squareElement.appendChild(rankLabel);
            }
            
            if (rank === 1) {
                const fileLabel = document.createElement('div');
                fileLabel.className = 'file-label';
                fileLabel.textContent = fileChar;
                fileLabel.style.position = 'absolute';
                fileLabel.style.bottom = '2px';
                fileLabel.style.right = '2px';
                fileLabel.style.fontSize = '10px';
                fileLabel.style.fontWeight = 'bold';
                squareElement.appendChild(fileLabel);
            }
            
            // Add event listeners
            squareElement.addEventListener('click', handleSquareClick);
            squareElement.addEventListener('dragover', handleDragOver);
            squareElement.addEventListener('drop', handleDrop);
            squareElement.addEventListener('dragstart', handleDragStart);
            
            boardElement.appendChild(squareElement);
        }
    }
    
    // Set up control buttons
    document.getElementById('reset-board').addEventListener('click', resetBoard);
    document.getElementById('clear-board').addEventListener('click', clearBoard);
    
    // Render initial position
    renderBoard();
}

function renderBoard() {
    const squares = document.querySelectorAll('.chess-square');
    
    squares.forEach(square => {
        const squareId = square.dataset.square;
        const piece = currentBoard[squareId];
        
        // Clear square content except labels
        const labels = square.querySelectorAll('.rank-label, .file-label');
        square.innerHTML = '';
        labels.forEach(label => square.appendChild(label));
        
        if (piece) {
            const pieceElement = document.createElement('span');
            pieceElement.textContent = PIECES[piece];
            pieceElement.draggable = true;
            pieceElement.style.cursor = 'grab';
            pieceElement.style.userSelect = 'none';
            
            // Definir cores específicas para cada time
            if (piece.startsWith('w')) {
                pieceElement.style.color = '#ffffff';
                pieceElement.style.textShadow = '2px 2px 4px rgba(0, 0, 0, 0.8)';
            } else {
                pieceElement.style.color = '#1a1a1a';
                pieceElement.style.textShadow = '1px 1px 2px rgba(255, 255, 255, 0.3)';
            }
            
            square.appendChild(pieceElement);
        }
    });
}

function handleSquareClick(event) {
    const square = event.currentTarget.dataset.square;
    
    if (selectedSquare) {
        if (selectedSquare === square) {
            // Deselect
            clearSelection();
        } else {
            // Move piece
            movePiece(selectedSquare, square);
            clearSelection();
        }
    } else if (currentBoard[square]) {
        // Select piece
        selectedSquare = square;
        event.currentTarget.classList.add('selected');
    }
}

function handleDragStart(event) {
    const square = event.target.parentElement.dataset.square;
    if (currentBoard[square]) {
        draggedPiece = {
            from: square,
            piece: currentBoard[square]
        };
        event.dataTransfer.effectAllowed = 'move';
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    event.currentTarget.classList.add('drag-over');
}

function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');
    
    const toSquare = event.currentTarget.dataset.square;
    
    if (draggedPiece && draggedPiece.from !== toSquare) {
        movePiece(draggedPiece.from, toSquare);
    }
    
    draggedPiece = null;
}

function movePiece(from, to) {
    if (currentBoard[from]) {
        currentBoard[to] = currentBoard[from];
        delete currentBoard[from];
        renderBoard();
    }
}

function clearSelection() {
    selectedSquare = null;
    document.querySelectorAll('.chess-square').forEach(square => {
        square.classList.remove('selected');
    });
}

// FEN to board position converter
function fenToPosition(fen) {
    const [position, turn, castling, enPassant, halfmove, fullmove] = fen.split(' ');
    const ranks = position.split('/');
    const board = {};
    
    const pieceMap = {
        'K': 'wK', 'Q': 'wQ', 'R': 'wR', 'B': 'wB', 'N': 'wN', 'P': 'wP',
        'k': 'bK', 'q': 'bQ', 'r': 'bR', 'b': 'bB', 'n': 'bN', 'p': 'bP'
    };
    
    for (let rank = 0; rank < 8; rank++) {
        let file = 0;
        const rankStr = ranks[rank];
        
        for (let i = 0; i < rankStr.length; i++) {
            const char = rankStr[i];
            
            if (isNaN(char)) {
                // It's a piece
                const fileChar = String.fromCharCode(97 + file); // a-h
                const rankNum = 8 - rank; // 8-1
                const square = fileChar + rankNum;
                board[square] = pieceMap[char];
                file++;
            } else {
                // It's a number (empty squares)
                file += parseInt(char);
            }
        }
    }
    
    return board;
}

// Exercise puzzle state
let exercisePuzzles = {};

// Create interactive exercise puzzle with real chess rules
function createExerciseBoard(containerId, fen) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    container.className = 'exercise-chess-board';
    
    // Initialize puzzle state
    exercisePuzzles[containerId] = {
        position: fenToPosition(fen),
        originalPosition: fenToPosition(fen),
        selectedSquare: null,
        solved: false,
        moveCount: 0,
        currentTurn: 'white' // Brancas começam
    };
    
    // Create board squares
    for (let rank = 8; rank >= 1; rank--) {
        for (let file = 0; file < 8; file++) {
            const fileChar = String.fromCharCode(97 + file); // a-h
            const square = fileChar + rank;
            
            const squareElement = document.createElement('div');
            const squareClass = `chess-square ${(rank + file) % 2 === 0 ? 'dark' : 'light'}`;
            
            squareElement.className = squareClass;
            squareElement.dataset.square = square;
            squareElement.dataset.board = containerId;
            
            // Add coordinate labels
            if (file === 0) {
                const rankLabel = document.createElement('div');
                rankLabel.className = 'rank-label';
                rankLabel.textContent = rank;
                squareElement.appendChild(rankLabel);
            }
            
            if (rank === 1) {
                const fileLabel = document.createElement('div');
                fileLabel.className = 'file-label';
                fileLabel.textContent = fileChar;
                squareElement.appendChild(fileLabel);
            }
            
            // Add click handlers for puzzle interaction
            squareElement.addEventListener('click', handlePuzzleClick);
            
            container.appendChild(squareElement);
        }
    }
    
    // Render initial position
    renderExerciseBoard(containerId, exercisePuzzles[containerId].position);
    
    // Store the solution and hint for this exercise
    exercisePuzzles[containerId].solution = getSolutionForExercise(containerId);
    exercisePuzzles[containerId].hint = getHintForExercise(containerId);
}

// Handle puzzle square clicks
function handlePuzzleClick(event) {
    const square = event.currentTarget.dataset.square;
    const boardId = event.currentTarget.dataset.board;
    const puzzle = exercisePuzzles[boardId];
    
    if (!puzzle || puzzle.solved) return;
    
    const currentPlayer = puzzle.currentTurn === 'white' ? 'w' : 'b';
    
    if (puzzle.selectedSquare) {
        if (puzzle.selectedSquare === square) {
            // Deselect
            clearPuzzleSelection(boardId);
        } else {
            // Try to move piece
            if (isValidMove(boardId, puzzle.selectedSquare, square)) {
                const lastMove = { from: puzzle.selectedSquare, to: square };
                if (makeMove(boardId, puzzle.selectedSquare, square)) {
                    clearPuzzleSelection(boardId);
                    // Switch turns
                    puzzle.currentTurn = puzzle.currentTurn === 'white' ? 'black' : 'white';
                    checkSolution(boardId, lastMove);
                }
            } else {
                // Show invalid move feedback
                showInvalidMove(boardId, square);
                // Try selecting new piece if it belongs to current player
                clearPuzzleSelection(boardId);
                if (puzzle.position[square] && puzzle.position[square].startsWith(currentPlayer)) {
                    selectSquare(boardId, square);
                }
            }
        }
    } else if (puzzle.position[square] && puzzle.position[square].startsWith(currentPlayer)) {
        // Select piece of current player
        selectSquare(boardId, square);
    }
}

// Select square
function selectSquare(boardId, square) {
    const puzzle = exercisePuzzles[boardId];
    puzzle.selectedSquare = square;
    
    const container = document.getElementById(boardId);
    const squareElement = container.querySelector(`[data-square="${square}"]`);
    squareElement.classList.add('selected');
}

// Clear selection
function clearPuzzleSelection(boardId) {
    const puzzle = exercisePuzzles[boardId];
    puzzle.selectedSquare = null;
    
    const container = document.getElementById(boardId);
    container.querySelectorAll('.chess-square').forEach(sq => {
        sq.classList.remove('selected', 'highlight');
    });
}

// Validate chess move according to piece rules
function isValidMove(boardId, from, to) {
    const puzzle = exercisePuzzles[boardId];
    const piece = puzzle.position[from];
    const targetPiece = puzzle.position[to];
    
    if (!piece || from === to) return false;
    
    // Can't capture own piece
    if (targetPiece && piece[0] === targetPiece[0]) return false;
    
    const pieceType = piece[1];
    const fromFile = from.charCodeAt(0) - 97;
    const fromRank = parseInt(from[1]) - 1;
    const toFile = to.charCodeAt(0) - 97;
    const toRank = parseInt(to[1]) - 1;
    
    const deltaFile = Math.abs(toFile - fromFile);
    const deltaRank = Math.abs(toRank - fromRank);
    
    switch (pieceType) {
        case 'P': // Pawn
            const direction = piece[0] === 'w' ? 1 : -1;
            const startRank = piece[0] === 'w' ? 1 : 6;
            
            if (deltaFile === 0) {
                // Moving forward
                if (targetPiece) return false; // Can't capture forward
                if (toRank === fromRank + direction) return true;
                if (fromRank === startRank && toRank === fromRank + 2 * direction) return true;
            } else if (deltaFile === 1 && toRank === fromRank + direction) {
                // Diagonal capture
                return !!targetPiece;
            }
            return false;
            
        case 'R': // Rook
            if (deltaFile === 0 || deltaRank === 0) {
                return !isPathBlocked(puzzle.position, from, to);
            }
            return false;
            
        case 'N': // Knight
            return (deltaFile === 2 && deltaRank === 1) || (deltaFile === 1 && deltaRank === 2);
            
        case 'B': // Bishop
            if (deltaFile === deltaRank) {
                return !isPathBlocked(puzzle.position, from, to);
            }
            return false;
            
        case 'Q': // Queen
            if (deltaFile === 0 || deltaRank === 0 || deltaFile === deltaRank) {
                return !isPathBlocked(puzzle.position, from, to);
            }
            return false;
            
        case 'K': // King
            return deltaFile <= 1 && deltaRank <= 1;
            
        default:
            return false;
    }
}

// Check if path is blocked
function isPathBlocked(position, from, to) {
    const fromFile = from.charCodeAt(0) - 97;
    const fromRank = parseInt(from[1]) - 1;
    const toFile = to.charCodeAt(0) - 97;
    const toRank = parseInt(to[1]) - 1;
    
    const deltaFile = toFile - fromFile;
    const deltaRank = toRank - fromRank;
    
    const stepFile = deltaFile === 0 ? 0 : (deltaFile > 0 ? 1 : -1);
    const stepRank = deltaRank === 0 ? 0 : (deltaRank > 0 ? 1 : -1);
    
    let currentFile = fromFile + stepFile;
    let currentRank = fromRank + stepRank;
    
    while (currentFile !== toFile || currentRank !== toRank) {
        const currentSquare = String.fromCharCode(97 + currentFile) + (currentRank + 1);
        if (position[currentSquare]) return true;
        
        currentFile += stepFile;
        currentRank += stepRank;
    }
    
    return false;
}

// Show invalid move feedback
function showInvalidMove(boardId, square) {
    const container = document.getElementById(boardId);
    const squareElement = container.querySelector(`[data-square="${square}"]`);
    
    squareElement.classList.add('invalid-move');
    setTimeout(() => {
        squareElement.classList.remove('invalid-move');
    }, 500);
}

// Make move
function makeMove(boardId, from, to) {
    const puzzle = exercisePuzzles[boardId];
    const piece = puzzle.position[from];
    
    if (!piece) return false;
    
    // Make the move
    puzzle.position[to] = piece;
    delete puzzle.position[from];
    puzzle.moveCount++;
    
    // Re-render board
    renderExerciseBoard(boardId, puzzle.position);
    
    return true;
}

// Check if puzzle is solved
function checkSolution(boardId, lastMove) {
    const puzzle = exercisePuzzles[boardId];
    const solution = getSolutionForExercise(boardId);
    
    if (!solution) {
        // Se não há solução específica, aceita qualquer movimento válido
        setTimeout(() => {
            showPuzzleResult(boardId, true);
        }, 500);
        return;
    }
    
    // Verifica se o movimento corresponde à solução
    const isCorrectMove = lastMove && 
                         lastMove.from === solution.from && 
                         lastMove.to === solution.to;
    
    setTimeout(() => {
        if (isCorrectMove) {
            showPuzzleResult(boardId, true);
        } else {
            showPuzzleResult(boardId, false);
            // Adiciona botão de resetar após movimento incorreto
            addResetButton(boardId);
        }
    }, 500);
}

// Show puzzle result
function showPuzzleResult(boardId, success) {
    const container = document.getElementById(boardId).parentElement;
    const resultDiv = container.querySelector('.puzzle-result') || document.createElement('div');
    
    if (!container.querySelector('.puzzle-result')) {
        resultDiv.className = 'puzzle-result';
        container.appendChild(resultDiv);
    }
    
    if (success) {
        resultDiv.innerHTML = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i>
                <strong>Excelente!</strong> Você encontrou a solução do puzzle!
            </div>
        `;
        resultDiv.className = 'puzzle-result success';
        exercisePuzzles[boardId].solved = true;
    } else {
        resultDiv.innerHTML = `
            <div class="error-message">
                <i class="fas fa-times-circle"></i>
                <strong>Você ainda não aprendeu o suficiente, tente denovo!</strong>
            </div>
        `;
        resultDiv.className = 'puzzle-result error';
    }
}

// Add puzzle controls
function addPuzzleControls(boardId) {
    const container = document.getElementById(boardId).parentElement;
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'puzzle-controls';
    controlsDiv.innerHTML = `
        <button class="btn btn-secondary btn-sm" onclick="resetPuzzle('${boardId}')">
            <i class="fas fa-undo"></i> Resetar
        </button>
        <button class="btn btn-primary btn-sm" onclick="showHint('${boardId}')">
            <i class="fas fa-lightbulb"></i> Dica
        </button>
    `;
    container.appendChild(controlsDiv);
}

// Reset puzzle
function resetPuzzle(boardId) {
    const puzzle = exercisePuzzles[boardId];
    puzzle.position = {...puzzle.originalPosition};
    puzzle.solved = false;
    puzzle.selectedSquare = null;
    puzzle.currentTurn = 'white';
    
    renderExerciseBoard(boardId, puzzle.position);
    clearPuzzleSelection(boardId);
    
    const container = document.getElementById(boardId).parentElement;
    const resultDiv = container.querySelector('.puzzle-result');
    if (resultDiv) {
        resultDiv.remove();
    }
    
    const resetButtonDiv = container.querySelector('.reset-button-container');
    if (resetButtonDiv) {
        resetButtonDiv.remove();
    }
}

// Add reset button after wrong move
function addResetButton(boardId) {
    const container = document.getElementById(boardId).parentElement;
    
    // Check if button already exists
    if (container.querySelector('.reset-button-container')) {
        return;
    }
    
    const resetButtonDiv = document.createElement('div');
    resetButtonDiv.className = 'reset-button-container';
    resetButtonDiv.style.textAlign = 'center';
    resetButtonDiv.style.marginTop = '10px';
    resetButtonDiv.innerHTML = `
        <button class="btn btn-warning btn-sm" onclick="resetPuzzle('${boardId}')" style="background-color: #dc3545; border-color: #dc3545; color: white;">
            <i class="fas fa-undo"></i> Reiniciar Tabuleiro
        </button>
    `;
    container.appendChild(resetButtonDiv);
}

// Show hint
function showHint(boardId) {
    const container = document.getElementById(boardId).parentElement;
    const hintDiv = container.querySelector('.puzzle-hint') || document.createElement('div');
    
    if (!container.querySelector('.puzzle-hint')) {
        hintDiv.className = 'puzzle-hint';
        container.appendChild(hintDiv);
    }
    
    hintDiv.innerHTML = `
        <div class="hint-message">
            <i class="fas fa-lightbulb"></i>
            <strong>Dica:</strong> Procure por táticas que forcem o adversário. Pense em sacrifícios, deflexões ou ataques duplos.
        </div>
    `;
    
    setTimeout(() => {
        hintDiv.style.opacity = '0';
        setTimeout(() => hintDiv.remove(), 300);
    }, 5000);
}

// Render exercise board with position
function renderExerciseBoard(containerId, position) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const squares = container.querySelectorAll('.chess-square');
    
    squares.forEach(square => {
        const squareId = square.dataset.square;
        const piece = position[squareId];
        
        // Clear square content except labels
        const labels = square.querySelectorAll('.rank-label, .file-label');
        square.innerHTML = '';
        labels.forEach(label => square.appendChild(label));
        
        if (piece) {
            const pieceElement = document.createElement('span');
            pieceElement.textContent = PIECES[piece];
            pieceElement.style.cursor = 'default';
            pieceElement.style.userSelect = 'none';
            pieceElement.style.fontSize = '2.5em';
            
            // Definir cores específicas para cada time
            if (piece.startsWith('w')) {
                pieceElement.style.color = '#ffffff';
                pieceElement.style.textShadow = '2px 2px 4px rgba(0, 0, 0, 0.8)';
            } else {
                pieceElement.style.color = '#1a1a1a';
                pieceElement.style.textShadow = '1px 1px 2px rgba(255, 255, 255, 0.3)';
            }
            
            square.appendChild(pieceElement);
        }
    });
}

function resetBoard() {
    currentBoard = {...INITIAL_POSITION};
    clearSelection();
    renderBoard();
}

function clearBoard() {
    currentBoard = {};
    clearSelection();
    renderBoard();
}

// Remove drag-over class when dragging leaves
document.addEventListener('dragleave', function(event) {
    if (event.target.classList.contains('chess-square')) {
        event.target.classList.remove('drag-over');
    }
});

// ===== FUNÇÕES PARA EXERCÍCIOS =====

// Reset board to initial position
function resetBoard(boardId) {
    const puzzle = exercisePuzzles[boardId];
    if (!puzzle) return;
    
    puzzle.position = {...puzzle.originalPosition};
    puzzle.selectedSquare = null;
    puzzle.solved = false;
    puzzle.moveCount = 0;
    puzzle.currentTurn = 'white';
    
    clearPuzzleSelection(boardId);
    renderExerciseBoard(boardId, puzzle.position);
    
    // Remove any hints or solution highlights
    const container = document.getElementById(boardId);
    container.querySelectorAll('.chess-square').forEach(sq => {
        sq.classList.remove('hint', 'last-move', 'valid-move');
    });
    
    showMessage(boardId, 'Tabuleiro resetado para posição inicial', 'info');
}

// Show hint for the exercise
function showHint(boardId) {
    const puzzle = exercisePuzzles[boardId];
    if (!puzzle || puzzle.solved) return;
    
    const hint = puzzle.hint;
    if (hint && hint.square) {
        // Clear previous hints
        const container = document.getElementById(boardId);
        container.querySelectorAll('.chess-square').forEach(sq => {
            sq.classList.remove('hint');
        });
        
        // Highlight hint square
        const hintSquare = container.querySelector(`[data-square="${hint.square}"]`);
        if (hintSquare) {
            hintSquare.classList.add('hint');
            setTimeout(() => {
                hintSquare.classList.remove('hint');
            }, 3000);
        }
        
        showMessage(boardId, hint.message, 'warning');
    } else {
        showMessage(boardId, 'Pense nas peças mais ativas e nos pontos fracos do adversário!', 'info');
    }
}

// Show solution for the exercise
function showSolution(boardId) {
    const puzzle = exercisePuzzles[boardId];
    if (!puzzle) return;
    
    const solution = puzzle.solution;
    if (solution) {
        // Highlight solution move
        const container = document.getElementById(boardId);
        container.querySelectorAll('.chess-square').forEach(sq => {
            sq.classList.remove('hint', 'last-move');
        });
        
        if (solution.from && solution.to) {
            const fromSquare = container.querySelector(`[data-square="${solution.from}"]`);
            const toSquare = container.querySelector(`[data-square="${solution.to}"]`);
            
            if (fromSquare && toSquare) {
                fromSquare.classList.add('hint');
                toSquare.classList.add('last-move');
            }
        }
        
        showMessage(boardId, `Solução: ${solution.move} - ${solution.explanation}`, 'success');
        puzzle.solved = true;
    } else {
        showMessage(boardId, 'Analise a coordenação das peças e procure por táticas!', 'info');
    }
}

// Get solution for specific exercise
function getSolutionForExercise(boardId) {
    const solutions = {
        'exercise1-board': {
            move: 'Nf5',
            from: 'f3',
            to: 'f5',
            explanation: 'O cavalo em f5 ataca múltiplos pontos e cria ameaças táticas decisivas.'
        },
        'exercise2-board': {
            move: 'Nf5',
            from: 'f3',
            to: 'f5',
            explanation: 'O cavalo em f5 domina o centro e prepara ataques nas casas escuras.'
        },
        'exercise3-board': {
            move: 'Nf5',
            from: 'f3',
            to: 'f5',
            explanation: 'Movimento central que ativa o cavalo e pressiona o adversário.'
        },
        'exercise4-board': {
            move: 'Nf5',
            from: 'f3',
            to: 'f5',
            explanation: 'Cavalo centralizado ganha força tática e controla pontos vitais.'
        },
        'exercise5-board': {
            move: 'Nf5',
            from: 'f3',
            to: 'f5',
            explanation: 'Posicionamento agressivo do cavalo que força respostas do adversário.'
        },
        'exercise6-board': {
            move: 'dxe5',
            from: 'd4',
            to: 'e5',
            explanation: 'Abre o centro e ativa as peças brancas, aproveitando o desenvolvimento superior.'
        },
        'exercise7-board': {
            move: 'Nf5',
            from: 'f3',
            to: 'f5',
            explanation: 'O cavalo move-se nas sombras para uma posição poderosa.'
        },
        'exercise8-board': {
            move: 'Bxf7+',
            from: 'd3',
            to: 'f7',
            explanation: 'Sacrifício clássico que expõe o rei preto e garante ataque decisivo.'
        },
        'exercise9-board': {
            move: 'Kd4',
            from: 'd3',
            to: 'd4',
            explanation: 'Centralização do rei no final, controlando casas importantes.'
        },
        'exercise10-board': {
            move: 'Nf5',
            from: 'f3',
            to: 'f5',
            explanation: 'Cavalo nas sombras revela seu verdadeiro poder tático.'
        }
    };
    
    return solutions[boardId] || null;
}

// Get hint for specific exercise
function getHintForExercise(boardId) {
    const hints = {
        'exercise6-board': {
            square: 'd4',
            message: 'Observe o peão d4 - ele pode ser a chave para abrir o centro!'
        },
        'exercise8-board': {
            square: 'd3',
            message: 'O bispo está bem posicionado para um sacrifício no rei adversário!'
        },
        'exercise9-board': {
            square: 'd3',
            message: 'Nos finais, o rei deve ser ativo - centralize-o!'
        }
    };
    
    return hints[boardId] || null;
}

// Show message to user
function showMessage(boardId, message, type = 'info') {
    // Create or update message element
    let messageEl = document.getElementById(`message-${boardId}`);
    if (!messageEl) {
        messageEl = document.createElement('div');
        messageEl.id = `message-${boardId}`;
        messageEl.className = 'exercise-message';
        
        const container = document.getElementById(boardId).parentElement;
        container.appendChild(messageEl);
    }
    
    // Set message content and style
    messageEl.textContent = message;
    messageEl.className = `exercise-message ${type}`;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (messageEl && messageEl.parentElement) {
            messageEl.remove();
        }
    }, 5000);
}

// ===== SISTEMA DE PUZZLE INTERATIVO =====

// Global puzzle state
let puzzleGames = {};
let correctMovesCounter = 0;

// Create interactive puzzle board
function createPuzzleBoard(containerId, fen, solution) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    container.className = 'puzzle-chess-board';
    
    // Initialize puzzle state
    puzzleGames[containerId] = {
        position: fenToPosition(fen),
        originalPosition: fenToPosition(fen),
        solution: solution,
        draggedPiece: null,
        draggedFrom: null,
        solved: false,
        playerColor: 'white' // sempre brancas por padrão
    };
    
    // Create board squares with coordinates
    for (let rank = 8; rank >= 1; rank--) {
        for (let file = 0; file < 8; file++) {
            const fileChar = String.fromCharCode(97 + file); // a-h
            const square = fileChar + rank;
            
            const squareElement = document.createElement('div');
            const squareClass = `chess-square ${(rank + file) % 2 === 0 ? 'dark' : 'light'}`;
            
            squareElement.className = squareClass;
            squareElement.dataset.square = square;
            squareElement.dataset.board = containerId;
            
            // Add drag and drop handlers
            squareElement.addEventListener('mousedown', handlePuzzleMouseDown);
            squareElement.addEventListener('mouseup', handlePuzzleMouseUp);
            squareElement.addEventListener('dragover', allowDrop);
            squareElement.addEventListener('drop', handlePuzzleDrop);
            
            container.appendChild(squareElement);
        }
    }
    
    // Render initial position
    renderPuzzleBoard(containerId, puzzleGames[containerId].position);
}

// Render puzzle board
function renderPuzzleBoard(containerId, position) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Clear all squares
    container.querySelectorAll('.chess-square').forEach(square => {
        square.innerHTML = '';
    });
    
    // Place pieces
    Object.entries(position).forEach(([square, piece]) => {
        const squareElement = container.querySelector(`[data-square="${square}"]`);
        if (squareElement && piece) {
            const pieceElement = document.createElement('span');
            pieceElement.textContent = PIECES[piece];
            pieceElement.style.cursor = piece.startsWith('w') ? 'grab' : 'default';
            pieceElement.style.userSelect = 'none';
            pieceElement.draggable = piece.startsWith('w'); // Só brancas arrastáveis
            
            // Cores das peças
            if (piece.startsWith('w')) {
                pieceElement.style.color = '#ffffff';
                pieceElement.style.textShadow = '2px 2px 4px rgba(0, 0, 0, 0.8)';
            } else {
                pieceElement.style.color = '#1a1a1a';
                pieceElement.style.textShadow = '1px 1px 2px rgba(255, 255, 255, 0.3)';
            }
            
            squareElement.appendChild(pieceElement);
        }
    });
}

// Handle mouse down for drag start
function handlePuzzleMouseDown(event) {
    const square = event.currentTarget.dataset.square;
    const boardId = event.currentTarget.dataset.board;
    const puzzle = puzzleGames[boardId];
    
    if (!puzzle || puzzle.solved) return;
    
    const piece = puzzle.position[square];
    if (piece && piece.startsWith('w')) { // Só peças brancas
        puzzle.draggedPiece = piece;
        puzzle.draggedFrom = square;
        event.currentTarget.classList.add('dragging');
    }
}

// Handle mouse up for drop
function handlePuzzleMouseUp(event) {
    const square = event.currentTarget.dataset.square;
    const boardId = event.currentTarget.dataset.board;
    const puzzle = puzzleGames[boardId];
    
    if (!puzzle || !puzzle.draggedFrom) return;
    
    // Clear dragging state
    const container = document.getElementById(boardId);
    container.querySelectorAll('.chess-square').forEach(sq => {
        sq.classList.remove('dragging');
    });
    
    // Check if valid drop
    if (puzzle.draggedFrom !== square) {
        processPuzzleMove(boardId, puzzle.draggedFrom, square);
    }
    
    // Reset drag state
    puzzle.draggedPiece = null;
    puzzle.draggedFrom = null;
}

// Allow drop
function allowDrop(event) {
    event.preventDefault();
}

// Handle drop
function handlePuzzleDrop(event) {
    event.preventDefault();
    // MouseUp handler will take care of the move
}

// Process puzzle move
function processPuzzleMove(boardId, from, to) {
    const puzzle = puzzleGames[boardId];
    if (!puzzle || puzzle.solved) return;
    
    const move = from + '-' + to;
    const isCorrect = move === puzzle.solution;
    
    if (isCorrect) {
        // Correct move
        correctMovesCounter++;
        document.getElementById('correct-moves-counter').textContent = correctMovesCounter;
        
        // Update position
        puzzle.position[to] = puzzle.position[from];
        delete puzzle.position[from];
        puzzle.solved = true;
        
        // Render new position
        renderPuzzleBoard(boardId, puzzle.position);
        
        // Show success message after 0.5s
        setTimeout(() => {
            showPuzzleStatus(boardId, 'Você evoluiu!', 'correct');
        }, 500);
        
    } else {
        // Incorrect move - show message after 0.5s
        setTimeout(() => {
            showPuzzleStatus(boardId, 'Movimento incorreto, tente novamente', 'incorrect');
        }, 500);
    }
}

// Show puzzle status and buttons
function showPuzzleStatus(boardId, message, type) {
    const statusElement = document.getElementById(`puzzle-status-${boardId.slice(-1)}`);
    const actionsElement = document.getElementById(`puzzle-actions-${boardId.slice(-1)}`);
    
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = `puzzle-status ${type}`;
    }
    
    if (actionsElement) {
        actionsElement.style.display = 'flex';
    }
}

// Retry puzzle
function retryPuzzle(boardId) {
    const puzzle = puzzleGames[boardId];
    if (!puzzle) return;
    
    // Reset puzzle state
    puzzle.position = {...puzzle.originalPosition};
    puzzle.solved = false;
    puzzle.draggedPiece = null;
    puzzle.draggedFrom = null;
    
    // Render original position
    renderPuzzleBoard(boardId, puzzle.position);
    
    // Hide status and actions
    const statusElement = document.getElementById(`puzzle-status-${boardId.slice(-1)}`);
    const actionsElement = document.getElementById(`puzzle-actions-${boardId.slice(-1)}`);
    
    if (statusElement) statusElement.textContent = '';
    if (actionsElement) actionsElement.style.display = 'none';
}

// Quit puzzle
function quitPuzzle(boardId) {
    // Hide actions
    const actionsElement = document.getElementById(`puzzle-actions-${boardId.slice(-1)}`);
    if (actionsElement) actionsElement.style.display = 'none';
    
    // Show quit message
    const statusElement = document.getElementById(`puzzle-status-${boardId.slice(-1)}`);
    if (statusElement) {
        statusElement.textContent = 'Puzzle abandonado. Use "Tentar novamente" para recomeçar.';
        statusElement.className = 'puzzle-status incorrect';
    }
}
