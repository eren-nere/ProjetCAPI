document.addEventListener('DOMContentLoaded', function () {
    // Charger le nom de la salle depuis le DOM
    const roomName = document.getElementById('room-name').textContent.trim();

    // Initialiser la WebSocket
    const ws = new WebSocket(`ws://${window.location.host}/ws/poker/${roomName}/`);

    // Gérer les messages reçus
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Message reçu :", data);
        if (data.type === "vote") {
            console.log(`${data.player} a voté : ${data.vote}`);
        } else if (data.type === "reveal") {
            console.log("Votes révélés :", data.votes);
        }
    };

    // Gérer les erreurs de WebSocket
    ws.onerror = function(error) {
        console.error("Erreur WebSocket :", error);
    };

    // Gérer la fermeture de la connexion
    ws.onclose = function() {
        console.warn("WebSocket fermée");
    };

    // Fonction pour envoyer un vote
    window.sendVote = function(player, vote) {
        ws.send(JSON.stringify({
            'type': 'vote',
            'player': player,
            'vote': vote,
        }));
    };

    // Fonction pour révéler les votes
    window.revealVotes = function() {
        ws.send(JSON.stringify({'type': 'reveal'}));
    };
});
