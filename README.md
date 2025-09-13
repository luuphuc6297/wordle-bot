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

### Basic Usage

#### Solve Daily Puzzle
```bash
python main.py solve
```

#### Simulate with Known Answer (Rich Display)
```bash
python main.py simulate --target CRANE --verbose
```

#### Analyze Word Entropy
```bash
python main.py analyze BRAIN
```

#### Run Performance Benchmarks
```bash
# Quick test (20 games)
python main.py benchmark --quick

# Full benchmark (100 games)
python main.py benchmark --games 100

# Stress test with difficult words
python main.py benchmark --stress
```

### Advanced Usage

#### Custom Time Budget
```bash
python main.py solve --time-budget 10.0 --verbose
```

#### JSON Output
```bash
python main.py solve --output-format json > results.json
```

#### Analyze Custom Word List
```bash
python main.py analyze STARE --answers my_words.txt
```

## 🏛️ Architecture

The project follows **Clean Architecture** principles:

```
wordle_bot/
├── core/
│   ├── domain/          # Business entities and models
│   └── use_cases/       # Application business logic
├── infrastructure/      # External interfaces
│   ├── api/            # Wordle API client
│   └── data/           # Word list management
├── config/             # Application configuration
├── utils/              # Shared utilities
└── tests/              # Comprehensive test suite
```

### Key Components

- **SolverEngine**: Core entropy-maximization algorithm
- **GameStateManager**: Tracks game state and filters possibilities
- **GameClient**: API adapter with retry logic and error handling
- **Orchestrator**: Coordinates the complete solving process
- **WordLexicon**: Singleton for managing word lists

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

### Adding New Features

1. **Domain Changes**: Add to `core/domain/models.py`
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