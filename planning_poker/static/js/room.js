let ws;

document.addEventListener('DOMContentLoaded', () => {
    const roomName = window.location.pathname.split('/')[2];
    ws = new WebSocket(`ws://${window.location.host}/ws/poker/${roomName}/`);

    const userInfoElement = document.getElementById('user-info');
    const pseudo = userInfoElement.getAttribute('data-pseudo');
    const creator = userInfoElement.getAttribute('data-creator');

    const revealButton = document.getElementById('reveal');
    const notVotedList = document.getElementById('not-voted-list'); 
    const featureContainer = document.getElementById('feature-container'); 
    const currentFeature = document.getElementById('current-feature'); 
    const resetButton = document.getElementById('reset'); 

    if (pseudo === creator && revealButton) {
        revealButton.style.display = 'block';
        revealButton.disabled = true;
        revealButton.classList.add('btn-secondary');
    }
    if (revealButton) {
        revealButton.addEventListener('click', () => {
            if (ws) {
                ws.send(JSON.stringify({
                    type: "reveal",
                }));
            } else {
                console.error("Websocket pas connecté.");
            }
        });
    }

    ws.onopen = () => {
        console.log("Websocket connecté");
    };

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Message reçu :", data);

    switch (data.type) {
        case "vote":
            console.log(`EVENT : ${data.player} a voté ${data.vote}`);
            updateNotVotedList(data.not_voted);

            if (data.all_voted && pseudo === creator && revealButton) {
                revealButton.disabled = false;
                revealButton.classList.remove('btn-secondary');
                revealButton.classList.add('btn-danger');
            }
            break;

        case "reveal":
            console.log("Votes reçus :", data.votes);
            displayVotes(data.votes);
            if (data.unanimity) {
                console.log("✅ Unanimité détectée. Passage à la prochaine fonctionnalité.");
                alert("✅ Vote validé ! Passage à la prochaine fonctionnalité...");
                hideVoteSelection();
                clearNotVotedList();
                loadNextFeature(data.feature);

            } else {
                console.log("❌ Pas d'unanimité. Recommencer le vote.");
                alert("❌ Vote non unanime... On revote pour cette fonctionnalité.");
                restartVoteUI();
            }
            break;

        case "not_voted_update":
            updateNotVotedList(data.not_voted);
            break;

        case "feature_update":
            console.log("Feature en cours :", data.feature);
            loadNextFeature(data.feature);
            break;

        case "final_backlog":
            alert("🎉 Toutes les fonctionnalités ont été votées !");
            console.log("Final backlog : ", data.final_backlog);
            window.location.href = data.url;
            break;

        case "error":
            alert(`⚠️ Erreur : ${data.message}`);
            break;

        default:
            console.error(`Type d'événement inconnu : ${data.type}`);
            break;
    }
};





    ws.onclose = () => {
        console.log("Websocket déconnecté");
    };

});

function sendVote(player, vote) {
    if (ws) {
        ws.send(JSON.stringify({
            type: "vote",
            player: player,
            vote: vote,
        }));
        highlightSelectedCard(vote);
    }
}

function displayVotes(votes) {
    const voteList = document.getElementById('vote-list');
    document.getElementById('reset').style.display = 'block';
    console.log("Quoicoubotes: ", votes);
    if (voteList) {
        voteList.style.display = 'hidden';
        votes.forEach(vote => {
            const cardContainer = document.createElement('div');
            cardContainer.className = 'col-3 text-center mb-3';

            const cardImage = document.createElement('img');
            cardImage.src = getCardImage(vote.vote);
            cardImage.alt = `Carte ${vote.vote}`;
            cardImage.className = 'img-fluid';
            cardImage.style.width = '100px';

            const playerName = document.createElement('p');
            playerName.textContent = vote.name;
            playerName.className = 'mt-2 font-weight-bold';

            cardContainer.appendChild(cardImage);
            cardContainer.appendChild(playerName);
            voteList.appendChild(cardContainer);
        });
    }
}

function updateNotVotedList(notVotedPlayers) {
    const notVotedList = document.getElementById('not-voted-list');
    if (notVotedList) {
        notVotedList.innerHTML = '';

        notVotedPlayers.forEach(player => {
            const listItem = document.createElement('li');
            listItem.textContent = player;
            listItem.className = 'list-group-item';
            notVotedList.appendChild(listItem);
        });
    }
}

function clearNotVotedList() {
    const notVotedList = document.getElementById('not-voted-list');
    if (notVotedList) {
        notVotedList.innerHTML = '';
    }
}

function highlightSelectedCard(vote) {
    const cards = document.querySelectorAll('.vote-card img');
    cards.forEach(card => {
        card.style.opacity = "0.3";
    });

    const selectedCard = document.querySelector(`#card-vote-${vote} img`);
    if (selectedCard) {
        selectedCard.style.opacity = "1";
    }
}

function getCardImage(voteValue) {
    const basePath = '/static/images/cards/';
    const cardMap = {
        0: 'cartes_0.svg',
        1: 'cartes_1.svg',
        2: 'cartes_2.svg',
        3: 'cartes_3.svg',
        5: 'cartes_5.svg',
        8: 'cartes_8.svg',
        13: 'cartes_13.svg',
        20: 'cartes_20.svg',
        40: 'cartes_40.svg',
        100: 'cartes_100.svg',
        'Café': 'cartes_cafe.svg',
        'Joker': 'cartes_interro.svg'
    };
    return basePath + (cardMap[voteValue]);
}

function hideVoteSelection() {
    const actionsContainer = document.getElementById('actions');
    if (actionsContainer) {
        actionsContainer.style.display = 'none';
    }
}

function showVoteSelection() {
    const actionsContainer = document.getElementById('actions');
    if (actionsContainer) {
        actionsContainer.style.display = 'block';
    }
}

function loadNextFeature(feature) {
    const featureContainer = document.getElementById('feature-container'); 
    const currentFeature = document.getElementById('current-feature');

    if (featureContainer && currentFeature) {
        currentFeature.textContent = feature
            ? `Fonctionnalité en cours : ${feature.feature || feature.name}`
            : "Toutes les fonctionnalités ont été votées.";
    }
}



function displayFinalBacklog(backlog) {
    const backlogContainer = document.getElementById('backlog-container');
    if (backlogContainer) {
        backlogContainer.innerHTML = "<h3>Backlog Final</h3>";

        backlog.forEach(feature => {
            const featureItem = document.createElement('p');
            featureItem.textContent = `Feature : ${feature.feature || feature.name}, Priority : ${feature.priority || "Non définie"}`;
            backlogContainer.appendChild(featureItem);
        });
    }
}

function restartVoteUI() {
    const revealButton = document.getElementById('reveal');
    if (revealButton) {
        revealButton.disabled = true;
        revealButton.classList.remove('btn-danger');
        revealButton.classList.add('btn-secondary');
    }
    hideVotes(); 
    showVoteSelection(); 
    document.getElementById('reset').style.display = 'none';
}
function hideVotes() {
    const voteList = document.getElementById('vote-list');
    if (voteList) voteList.innerHTML = ''; 
}



