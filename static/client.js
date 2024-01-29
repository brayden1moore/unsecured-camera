let currentFeed;
let firstLoad = true;
document.addEventListener("DOMContentLoaded", function() {
    const feed = document.getElementById("feed");
    feed.style.width = "80px";
    feed.style.height = "50px";
    feed.src = loadingGif;
    feed.style.opacity = "0.2";
    const infoDiv = document.getElementById("info");
    const infoText = document.getElementById("info-text");
    infoText.style.opacity = "0";

    const countryElement = document.getElementById("country");
    
    const locationName = document.getElementById('location-name');
    locationName.textContent = page_title;

    let contentTypeChecked = false;
    let isJpeg = false;
    function refreshImage() {
        if (!isJpeg && !contentTypeChecked) {
            let xhr = new XMLHttpRequest();
            xhr.open('HEAD', newUrl, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    if (xhr.getResponseHeader('Content-Type') === 'image/jpeg') {
                        img.src = newUrl + "?r=" + new Date().getTime();
                        if (firstLoad){
                            countryElement.textContent = "connecting..."; 
                        }
                        isJpeg = true;
                        contentTypeChecked = true;
                    }
                }
            };
            xhr.send();
        } else if (isJpeg && contentTypeChecked) {
            img.src = newUrl + "?r=" + new Date().getTime();
        }
    }
    
    const img = new Image();
    img.onload = function() {
        if (firstLoad) {
            infoDiv.style.opacity = "0";
        }
        firstLoad = false;
        old = newUrl;
        setTimeout(() => {
            feed.src = this.src;
            locationName.textContent = location_name;
            feed.style.width = "100%";
            feed.style.height = "70%";
            feed.style.opacity = "1";
            infoDiv.style.opacity = "1";
        }, 100);
        const infoText = document.getElementById("info-text");
        infoText.style.opacity = "1";
        
        setTimeout(refreshImage, 500);
        country.textContent = country_name;
    };
    
    img.onerror = function(event) {
        feed.style.width = "80px";
        feed.style.height = "50px";
        feed.src = loadingGif;
        feed.style.opacity = "0.2";
        infoText.style.opacity = "0";
        locationName.textContent = page_title;
        console.log("Image loading failed:", event);
        
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('new') === 'false') {
            countryElement.textContent = "couldn't connect.";
        }
        else {
            window.location.href = "?new=true";
        }
    };
    
    img.src = newUrl;
});


// Time count
document.addEventListener("DOMContentLoaded", function() {
    setInterval(() => {
    const now = new Date();
    const options = { 
        timeZone: timezone, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: true
    };
    const timeString = now.toLocaleTimeString('en-US', options);
    document.getElementById("time").textContent = timeString;
    }, 200);
});

// Copy link
document.addEventListener("DOMContentLoaded", function() {
    const shareIcon = document.getElementById("share");
    const copiedText = document.getElementById("copied");

    shareIcon.addEventListener("click", function() {
        const id = this.getAttribute("data-id");
        const urlToCopy = `${window.location.origin}/?new=false&id=${id}`;
        
        navigator.clipboard.writeText(urlToCopy).then(() => {
            console.log("URL copied to clipboard");
            shareIcon.className = "fa-solid fa-check";
            //copiedText.style.visibility = "visible";
        }).catch(err => {
            console.log("Could not copy text: ", err);
        });
    });
});

// Connect vs search
document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    const countryElement = document.getElementById("country");

    if (urlParams.get('new') === 'false') {
        countryElement.textContent = "connecting...";
    }
});


// Fullscreen
document.addEventListener("DOMContentLoaded", function() {
const feed = document.getElementById("feed");
let isFullscreen = false; 

function toggleFullScreen() {
    if (!isFullscreen) {
        if (this.requestFullscreen) {
            this.requestFullscreen();
        } else if (this.mozRequestFullScreen) {
            this.mozRequestFullScreen();
        } else if (this.webkitRequestFullscreen) {
            this.webkitRequestFullscreen();
        } else if (this.msRequestFullscreen) {
            this.msRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
}

feed.addEventListener("click", toggleFullScreen);
feed.addEventListener("touchstart", toggleFullScreen);

document.addEventListener("fullscreenchange", function() {
    isFullscreen = !isFullscreen;
});
});

// Change feed on space bar press
document.addEventListener('keydown', function(event) {
    if (event.keyCode === 32) { 
    window.location.href = '/?new=true';
    }
});

// Show more info
document.addEventListener('DOMContentLoaded', function() {
const infoText = document.getElementById('info-text');
const additionalInfo = document.getElementById('additional-info');
const showMore = document.getElementById('show-more');
const moreButton = document.getElementById('more-button');

// Initial setup
additionalInfo.style.height = '0';
additionalInfo.style.overflow = 'hidden';
additionalInfo.style.transition = 'height 0.3s ease-in-out';

showMore.addEventListener('click', function() {
    if (additionalInfo.style.height === '0px') {
    const scrollHeight = additionalInfo.scrollHeight;
    additionalInfo.style.height = `${scrollHeight}px`;
    showMore.innerHTML = 'less <i style="margin-bottom:20px; color:rgb(53, 53, 53);" id="more-button" class="fa-solid fa-caret-up"></i>';
    } else {
    additionalInfo.style.height = '0';
    showMore.innerHTML = 'more <i style="margin-bottom:20px; color:rgb(53, 53, 53);" id="more-button" class="fa-solid fa-caret-down"></i>';
    }
});
});
