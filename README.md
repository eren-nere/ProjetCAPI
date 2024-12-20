
# Planning Poker

Un outil interactif pour la planification agile utilisant des cartes de poker.

## 🚀 Lancer le projet avec Docker Compose

### Prérequis
1. [Docker](https://www.docker.com/) installé sur votre machine.
2. [Docker Compose](https://docs.docker.com/compose/) installé.

### Étapes
1. Clonez ce dépôt sur votre machine locale :
   ```bash
   git clone https://github.com/eren-nere/ProjetCAPI.git
   cd planning-poker
   ```

2. Démarrez les services avec Docker Compose :
   ```bash
   docker-compose up -d
   ```

3. Accédez à l'application sur [http://localhost:8000](http://localhost:8000).

   - Redis est configuré pour fonctionner en arrière-plan en tant que service sous le hostname `redis`.

---

## 📖 Documentation

La documentation complète du projet est disponible ici :
[ProjetCAPI Documentation](https://eren-nere.github.io/ProjetCAPI)

---

## 🛠️ Développement

Pour développer localement :
1. Installez les dépendances Python avec `pip` :
   ```bash
   pip install -r requirements.txt
   ```
2. Lancez les migrations et démarrez le serveur Django :
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
3. Faites tourner un serveur Redis en arrière-plan :
   ```bash
   redis-server
   ```
---

## 🐳 Déploiement Docker

Pour déployer votre propre image Docker :
1. Construisez l'image :
   ```bash
   docker build -t planning-poker .
   ```
2. Démarrez un conteneur :
   ```bash
   docker run -p 8000:8000 planning-poker
   ```
   

