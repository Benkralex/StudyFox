# Requirements
- Python 3
- Git
- Docker

# Installation
1. `git clone --branch v2.0.1-beta --single-branch https://github.com/Benkralex/StudyFox.git studyfox`
2. `cd studyfox`
3. `docker buildx build -t studyfox:latest .`
4. `docker run -v .\src\instance\db.db:/app/instance/db.db -p 5000:8000 --name studyfox studyfox:latest`

# Server Start
1. `docker start studyfox`
