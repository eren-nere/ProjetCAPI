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
                console.log("✅ Passage à la prochaine fonctionnalité :", data.next_feature);
                loadNextFeature(data.next_feature);
                alert("✅ Passage à la prochaine fonctionnalité.");
                hideVoteSelection();
                clearNotVotedList();
            } else {
                console.log("❌ Condition non atteinte. On revote pour la fonctionnalité actuelle.");
                alert("❌ Condition non atteinte. Revote pour cette fonctionnalité.");
                restartVoteUI();
            }
            break;



        case "final_backlog":
            alert("🎉 Toutes les fonctionnalités ont été votées !");
            console.log("Final backlog : ", data.final_backlog);

            if (data.url) {
                window.location.href = data.url;
            } else {
                displayFinalBacklog(data.final_backlog);
            }
            break;



        case "not_voted_update":
            updateNotVotedList(data.not_voted);
            break;

        case "feature_update":
            console.log("Prochaine fonctionnalité reçue :", data.feature);
            loadNextFeature(data.feature);
            clearNotVotedList();
            break;

        case "redirect":
            console.log("Redirection vers :", data.url);
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
        200: 'cartes_cafe.svg'
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
    const currentFeature = document.getElementById('current-feature');
    if (currentFeature) {
        currentFeature.textContent = feature
            ? `Fonctionnalité en cours : ${feature.feature || feature.name}`
            : "Toutes les fonctionnalités ont été votées.";
    }
    console.log("Chargement de la nouvelle fonctionnalité :", feature);
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

function displayFinalBacklog(backlog) {
    const roomName = window.location.pathname.split('/')[2];
    document.location.href = `/final_backlog/${roomName}/`;
}