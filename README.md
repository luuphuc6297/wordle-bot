# Wordle Bot - Autonomous Puzzle Solver

An intelligent Wordle-solving bot that uses **information theory** and **entropy maximization** to find optimal guesses and solve puzzles efficiently.

## 🎯 Overview

This bot leverages **Shannon entropy** to systematically narrow down the space of possible answers, transforming Wordle from a luck-based game into a deterministic problem of information maximization. By consistently selecting guesses that yield the most information, the bot can solve puzzles in an average of **~3.5 turns**.

### Key Features

- **🧠 Entropy-based Strategy**: Uses information theory to calculate the most informative guess
- **⚡ Optimized Performance**: Pre-computed first guess (SALET) + parallel processing
- **🏗️ Clean Architecture**: Modular design with clear separation of concerns
- **🔄 API Integration**: Interfaces with Wordle APIs for real gameplay
- **🎮 Rich Console Display**: Beautiful real-time game visualization with emoji feedback
- **📊 Comprehensive Benchmarking**: Performance testing with detailed statistics and analysis
- **🧪 Extensive Testing**: Comprehensive test coverage, especially for edge cases
- **🐳 Containerized**: Docker support for easy deployment
- **📈 Analysis Tools**: Built-in tools for analyzing guess effectiveness and algorithm performance
- **🌐 Online & Offline Modes**: Support for both API-based and simulation-based gameplay

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip
- Docker (optional, for containerized deployment)

### Installation

1. **Clone and setup**:
```bash
cd /Users/luuphuc/Projects/wordle_bot
pip install -r requirements.txt
```

2. **Verify installation**:
```bash
python main.py --version
```

## 🎮 Game Modes

### Online Modes (Real API)
These modes interact with the actual Wordle API:

#### Daily Puzzle Mode
```bash
# Solve today's daily puzzle
python main.py solve

# With verbose output
python main.py solve --verbose --output-format json
```

#### Random Game Mode
```bash
# Play a random game via API
python main.py play-random

# With custom time budget
python main.py play-random --time-budget 10.0 --verbose
```

#### Word Target Mode
```bash
# Play against a specific word
uv run python main.py play-word --target CRANE

# Play against multiple words
uv run python main.py play-word --target CRANE AUDIO ZEBRA
```

### Offline Modes (Simulation)
These modes run locally without API calls:

#### Simulation Mode
```bash
# Simulate solving with known answer
uv run python main.py simulate --target CRANE

# With verbose output and JSON format
uv run python main.py simulate --target AUDIO --verbose --output-format json
```

#### Analysis Mode
```bash
# Analyze word entropy
python main.py analyze CRANE

# Analyze with custom word list
python main.py analyze STARE --answers my_words.txt
```

## 📊 Benchmarking & Analytics

### Offline Benchmarking
```bash
# Quick test (20 games)
uv run python main.py benchmark --quick

# Full benchmark (100 games)
uv run python main.py benchmark --games 100

# Stress test with difficult words
uv run python main.py benchmark --stress

# Save results to file
uv run python main.py benchmark --games 50 --output results.json
```

### Online Benchmarking
```bash
# Random mode benchmark (3 games)
python main.py online-benchmark --api-mode random --games 3

# Daily mode benchmark (automatically limited to 1 game)
python main.py online-benchmark --api-mode daily --games 10

# Word mode benchmark with specific targets
python main.py online-benchmark --api-mode word --target-words CRANE AUDIO ZEBRA
```

### Analytics
```bash
# Strategy analysis
uv run python main.py analytics --analysis-type strategy

# Word difficulty analysis
uv run python main.py analytics --analysis-type difficulty --sample-size 10

# Online analytics with daily API
uv run python main.py online-analytics --api-mode daily --analysis-type difficulty
```

## 🏛️ Architecture

The project follows **Clean Architecture** principles with a modular structure:

```
wordle_bot/
├── main.py                   # Main entry point
├── pyproject.toml            # Project configuration
├── pyrightconfig.json        # Type checking configuration
├── uv.lock                   # Dependency lock file
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Container definition
├── .pre-commit-config.yaml   # Pre-commit hooks
├── LICENSE                   # MIT License
├── README.md                 # This documentation
│
├── config/                   # Application configuration
│   └── settings.py           # Settings and environment variables
│
├── core/                     # Core business logic
│   │
│   ├── algorithms/           # Core algorithms and engines
│   │   ├── analytics_engine.py      # Advanced analytics
│   │   ├── benchmark_engine.py      # Performance benchmarking
│   │   ├── dependency_container.py  # Dependency injection
│   │   ├── solver_engine.py         # Core entropy algorithm
│   │   │
│   │   ├── orchestrator/            # Main orchestrator
│   │   │   ├── orchestrator.py      # Main coordinator
│   │   │   └── modes/               # Game mode handlers
│   │   │       ├── __init__.py
│   │   │       ├── base_handler.py  # Abstract base handler
│   │   │       ├── daily_handler.py # Daily puzzle handler
│   │   │       ├── offline_handler.py # Offline simulation handler
│   │   │       ├── random_handler.py # Random game handler
│   │   │       └── word_handler.py   # Word target handler
│   │   │
│   │   └── state_manager/           # Game state management
│   │       ├── base.py              # Base game state manager
│   │       ├── daily.py             # Daily-specific state manager
│   │       └── strategies.py        # Filtering strategies
│   │
│   ├── domain/               # Business entities and models
│   │   ├── constants.py      # Application constants
│   │   ├── models.py         # Domain models
│   │   └── types.py          # Type definitions (TypedDict)
│   │
│   └── use_cases/            # Application business logic
│       ├── __init__.py
│       ├── daily.py          # Daily mode entry point
│       ├── offline.py        # Offline simulation entry point
│       ├── random.py         # Random mode entry point
│       └── word.py           # Word target mode entry point
│
├── infrastructure/           # External interfaces
│   ├── api/                  # Wordle API client
│   │   └── game_client.py    # HTTP client with retry logic
│   └── data/                 # Word list management
│       ├── __init__.py
│       ├── allowed.txt       # Allowed guess words
│       ├── answers.txt       # Answer words
│       └── word_lexicon.py   # Word list manager
│
├── utils/                    # Shared utilities
│   ├── display.py            # Console display and formatting
│   └── logging_config.py     # Logging configuration
│
└── tests/                    # Comprehensive test suite
	   ├── __init__.py
	   ├── test_models.py        # Domain model tests
       └── test_solver_engine.py # Solver algorithm tests
```

### Key Components

- **Orchestrator**: Main coordinator with mode-specific handlers
- **Mode Handlers**: Specialized handlers for each game mode
  - `DailyHandler`: Handles daily puzzle solving
  - `RandomHandler`: Handles random game playing
  - `WordHandler`: Handles word target games
  - `OfflineHandler`: Handles offline simulations
- **State Managers**: Game state management with filtering strategies
- **SolverEngine**: Core entropy-maximization algorithm
- **GameClient**: API adapter with retry logic and error handling
- **WordLexicon**: Singleton for managing word lists
- **DependencyContainer**: Manages and injects dependencies

## 🧮 Algorithm Details

### Information Theory Approach

The bot uses **Shannon entropy** to measure uncertainty:

```
H(guess) = -Σ p(i) × log₂(p(i))
```

Where `p(i)` is the probability of each possible feedback pattern.

### Optimization Strategies

1. **Pre-computed First Guess**: SALET is optimal for minimizing average guesses
2. **Time-budgeted Calculation**: Respects strict time constraints per turn
3. **Parallel Processing**: NumPy + Threading for maximum performance on macOS
4. **Smart Fallbacks**: Graceful degradation when time budget is exceeded

### Feedback Simulation

Critical algorithm that handles **duplicate letters correctly**:

```python
def _simulate_feedback(self, guess: str, answer: str) -> str:
    # Two-pass algorithm:
    # 1. Mark exact matches (green)
    # 2. Mark present letters (yellow) with remaining counts
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# All tests
python -m pytest tests/ -v

# Specific test category
python -m pytest tests/test_solver_engine.py -v

# With coverage
python -m pytest tests/ --cov=core --cov=infrastructure
```

### Critical Test Cases

The test suite includes **extensive edge cases** for duplicate letter handling:

- `SPEED` vs `ERASE` → `-o+++`
- `GEESE` vs `CRANE` → `--o--`
- `ALLEY` vs `LLAMA` → `-++--`

## 🐳 Docker Deployment

### Production Deployment
```bash
# Build and run
docker-compose up wordle-bot

# View logs
docker-compose logs -f wordle-bot
```

### Development Environment
```bash
# Start development container
docker-compose --profile dev up -d wordle-bot-dev

# Access shell
docker-compose exec wordle-bot-dev bash
```

### Running Tests
```bash
docker-compose --profile test run --rm wordle-bot-test
```

## ⚙️ Configuration

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WORDLE_API_BASE_URL` | `https://wordle.votee.dev:8000` | API endpoint |
| `SOLVER_TIME_BUDGET_SECONDS` | `5.0` | Max time per guess calculation |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LOG_JSON_FORMAT` | `false` | Enable structured JSON logs |
| `SOLVER_MAX_WORKERS` | `auto` | Thread pool size |

## 📊 Performance Metrics

### Typical Performance
- **Average Turns**: ~3.5
- **Success Rate**: >99%
- **Time per Turn**: 2-5 seconds
- **First Guess**: SALET (pre-computed)

### Entropy Examples
- **SALET** (first guess): ~5.89 bits
- **STARE**: ~5.83 bits
- **CRANE**: ~5.70 bits

### Benchmark Results Format

The bot provides detailed benchmark results with clear distribution:

```json
{
  "games_played": 3,
  "games_won": 3,
  "win_rate": 100.0,
  "avg_guesses": 3.67,
  "distribution": {
    "3_guesses": 1,    // 1 game solved in 3 guesses
    "4_guesses": 2,    // 2 games solved in 4 guesses
    "losses": 0        // 0 games failed
  }
}
```

## 🔬 Analysis Tools

### Word Analysis
```bash
# Analyze specific word
python main.py analyze CRANE

# Compare multiple words
for word in CRANE STARE SALET; do
    echo "=== $word ==="
    python main.py analyze $word
done
```

### Simulation Testing
```bash
# Test against known answers
python main.py simulate AUDIO
python main.py simulate ZEBRA --verbose
```

## 🛠️ Development

### Code Style
- **No comments in Vietnamese** (per project rules)
- **SOLID principles** adherence
- **High reusability** focus
- **Consistent naming** conventions
- **Type safety** with comprehensive TypedDict definitions

### Adding New Features

1. **Domain Changes**: Add to `core/domain/`
2. **Business Logic**: Extend use cases in `core/use_cases/`
3. **External Integrations**: Add to `infrastructure/`
4. **Tests**: Add corresponding tests with edge cases

### Performance Considerations

- **Memory Usage**: Word lists loaded once (singleton pattern)
- **CPU Optimization**: Parallel entropy calculations
- **Time Constraints**: Hard limits with graceful degradation

## 🚨 Error Handling

The bot includes robust error handling:

- **API Failures**: Automatic retry with exponential backoff
- **Invalid Responses**: Graceful parsing with fallbacks
- **Time Budget**: Hard limits prevent infinite calculations
- **Data Validation**: Pydantic models ensure data integrity
- **Type Safety**: Comprehensive type checking with pyright

## 📈 Monitoring

### Structured Logging

Enable JSON logging for production monitoring:

```bash
LOG_JSON_FORMAT=true python main.py solve
```

### Key Metrics Logged
- Turn duration
- Remaining candidates after each guess
- API retry counts
- Entropy calculations

## 🤝 Contributing

1. Follow existing code patterns
2. Add tests for new functionality
3. Ensure all tests pass
4. Update documentation

## 📝 License

This project implements academic research in information theory applied to word games.

## 🔗 References

- Shannon, C.E. (1948). "A Mathematical Theory of Communication"
- Optimal Wordle strategies: Information theory analysis
- Clean Architecture principles (Robert C. Martin)

---

**Built with ❤️ and lots of entropy calculations**
