document.addEventListener('DOMContentLoaded', function () {
    const roomName = document.getElementById('room-name').textContent.trim();

    const ws = new WebSocket(`ws://${window.location.host}/ws/poker/${roomName}/`);

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Message reçu :", data);
        if (data.type === "vote") {
            console.log(`${data.player} a voté : ${data.vote}`);
        } else if (data.type === "reveal") {
            console.log("Votes révélés :", data.votes);
        }
    };

    ws.onerror = function(error) {
        console.error("Erreur WebSocket :", error);
    };

    ws.onclose = function() {
        console.warn("WebSocket fermée");
    };

    window.sendVote = function(player, vote) {
        ws.send(JSON.stringify({
            'type': 'vote',
            'player': player,
            'vote': vote,
        }));
    };

    window.revealVotes = function() {
        ws.send(JSON.stringify({'type': 'reveal'}));
    };
});
