# Contributing to Smart Travel Planner AI

Thank you for your interest in contributing to Smart Travel Planner AI! 🎉

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/smart-travel-planner-ai.git
   cd smart-travel-planner-ai
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Make your changes**
5. **Run tests** to ensure everything works:
   ```bash
   pytest
   ```
6. **Commit your changes**:
   ```bash
   git commit -m 'Add amazing feature'
   ```
7. **Push to the branch**:
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request**

## 🧪 Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

## 📝 Code Standards

- **Code Formatting**: Use Black for consistent formatting
  ```bash
  black .
  ```
- **Style Guidelines**: Follow PEP 8
  ```bash
  flake8 .
  ```
- **Type Hints**: Add type hints to all functions
  ```bash
  mypy src/
  ```
- **Testing**: Write tests for new features
  ```bash
  pytest
  ```
- **Documentation**: Update documentation for new features

## 🏗️ Project Structure

```
smart-travel-planner-ai/
├── src/
│   ├── agents/              # AI agent implementations
│   │   ├── supervisor.py    # Main orchestrator
│   │   ├── query_parser.py  # Query processing
│   │   ├── itinerary_agent.py # Itinerary generation
│   │   └── critique_agent.py   # Quality evaluation
│   ├── core/               # Core application logic
│   ├── models/             # Data models and state
│   └── services/           # External integrations
├── infrastructure/
│   └── terraform/          # AWS infrastructure code
├── tests/                  # Test suite
├── app.py                  # Main Streamlit application
├── app_enhanced.py         # Enhanced UI version
└── requirements.txt        # Python dependencies
```

## 🐛 Bug Reports

When reporting bugs, please include:

- **Python version** (`python --version`)
- **Operating system**
- **AWS region** (if applicable)
- **Error messages** (full stack trace)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**

Use the GitHub issue tracker with the "bug" label.

## 💡 Feature Requests

For feature requests, please provide:

- **Clear description** of the feature
- **Use case** or problem it solves
- **Possible implementation** approach
- **Alternative solutions** considered

Use the GitHub issue tracker with the "enhancement" label.

## 🧪 Testing Guidelines

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

### Writing Tests
- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names
- Test both happy path and edge cases
- Mock external API calls

### Test Categories
- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

## 🌐 API Integration

When adding new external APIs:

1. **Add to services module**: `src/services/external_apis.py`
2. **Implement fallback**: Always provide mock data fallback
3. **Add configuration**: Environment variables in `.env.example`
4. **Document usage**: Update README with API requirements
5. **Add tests**: Mock the API responses in tests

## 🏗️ Infrastructure Changes

For Terraform/AWS changes:

1. **Test locally**: Use `terraform plan` first
2. **Document costs**: Update cost estimates in README
3. **Security review**: Ensure minimal IAM permissions
4. **Backward compatibility**: Don't break existing deployments

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] Branch is up to date with main

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### 🤖 **AI & Agent Improvements**
- Enhanced prompt engineering
- New agent types (e.g., booking agent)
- Improved confidence scoring
- Multi-language support

### 🌐 **External Integrations**
- Additional travel APIs
- Social media integration
- Calendar integration
- Payment processing

### 🎨 **Frontend Enhancements**
- Mobile app development
- Advanced visualizations
- Interactive maps
- PDF export functionality

### ☁️ **Infrastructure & DevOps**
- CI/CD pipelines
- Monitoring improvements
- Performance optimizations
- Security enhancements

### 📚 **Documentation**
- Tutorial videos
- API documentation
- Architecture diagrams
- Deployment guides

## 🏆 Recognition

Contributors will be recognized in:
- README contributors section
- Release notes
- Project documentation

Top contributors may be invited to join the core team!

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check the project wiki

## 📄 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful**: Treat everyone with respect and kindness
- **Be constructive**: Provide helpful feedback and suggestions
- **Be collaborative**: Work together towards common goals
- **Be inclusive**: Welcome contributors from all backgrounds

## 🙏 Thank You

Thank you for contributing to Smart Travel Planner AI! Your efforts help make travel planning smarter and more accessible for everyone. 🌍✈️

---

**Questions?** Feel free to open an issue or reach out to the maintainers!
