// static/app.js

let map;
let markers = [];
let parkingLots = [];
let parking_lots = [];

function initMap() {
    map = L.map('map').setView([10.762622, 106.660172], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    L.control.locate({
        locateOptions: {
            enableHighAccuracy: true
        }
    }).addTo(map);

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            fetch(`/api/parking_lots/?latitude=${userLat}&longitude=${userLng}&search=`)
                .then(response => response.json())
                .then(data => {
                    parking_lots = data;
                    data.forEach(lot => {
                        addMarker(lot);
                    });
                    displayParkingLots(data);
                });
        });
    } else {
        loadParkingLots(10.762622, 106.660172); // Default location if geolocation is not supported
    }
}

function loadParkingLots(latitude, longitude, search = '') {
    fetch(`/api/parking_lots/?latitude=${latitude}&longitude=${longitude}&search=${search}`)
        .then(response => response.json())
        .then(data => {
            parkingLots = data;
            // data.forEach(lot => {
            //     addMarker(lot);
            // });
            displayParkingLots(data);
        });
}

function addMarker(lot) {
    const marker = L.marker([lot.latitude, lot.longitude]).addTo(map);
    marker.bindPopup(`
        <div>
            <strong>${lot.name}</strong><br>${lot.location}<br>
            <button onclick="getDirections(${lot.latitude}, ${lot.longitude})">Chỉ đường</button>
        </div>
    `);
    markers.push({
        marker: marker,
        name: lot.name,
        location: lot.location,
    });
}

function displayParkingLots(parkingLots) {
    const parkingList = document.querySelector('.parking-list');
    parkingList.innerHTML = '';

    parkingLots.forEach(lot => {
        const parkingItem = `
            <div class="parking-item card mb-3">
                <a href="/accounts/create-reservation/${lot.id}" style="text-decoration: none; color: inherit;">
                    <div class="row no-gutters">
                        <div class="col-md-4">
                            <img src="${lot.image_url}" alt="${lot.name}" class="img-fluid-custom">
                        </div>
                        <div class="col-md-8">
                            <div class="card-body">
                                <h5 class="card-title">${lot.name}</h5>
                                <p class="card-text">Địa chỉ: ${lot.location}</p>
                                <p class="card-text">Số lượng bãi đậu: ${lot.total_capacity}</p>
                                <p class="card-text">Giá vé gửi xe: ${lot.price_for_first_two_hours}/2 giờ đầu</p>
                                <p class="card-text">Mở cửa: ${lot.opening_time} - Đóng cửa: ${lot.closing_time}</p>
                                <p class="card-text">Khoảng cách từ vị trí hiện tại: ${lot.distance.toFixed(2)} km</p>
                            </div>
                        </div>
                    </div>
                </a>
            </div>
        `;
        parkingList.innerHTML += parkingItem;
    });
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Đường kính trái đất (đơn vị: km)
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const d = R * c; // Khoảng cách giữa hai điểm (đơn vị: km)
    return d;
}

function searchParkingLots() {
    const input = document.getElementById('search-input').value.toLowerCase();
    let nearestMarker = null; // Biến lưu trữ marker gần nhất
    let nearestDistance = Infinity; // Biến lưu trữ khoảng cách gần nhất

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;

            markers.forEach(item => {
                const distance = calculateDistance(userLat, userLng, item.marker.getLatLng().lat, item.marker.getLatLng().lng);
                if (item.name.toLowerCase().includes(input) || item.location.toLowerCase().includes(input)) {
                    item.marker.setOpacity(1); // Hiển thị marker
                    if (distance < nearestDistance) {
                        nearestDistance = distance;
                        nearestMarker = item.marker;
                    }
                } else {
                    item.marker.setOpacity(0); // Ẩn marker
                }
            });

            if (nearestMarker) {
                map.setView(nearestMarker.getLatLng(), 14); // Đặt trung tâm bản đồ tại marker gần nhất
                nearestMarker.openPopup(); // Mở popup của marker gần nhất
            }
            loadParkingLots(userLat, userLng, input);
        });
    } else {
        loadParkingLots(10.762622, 106.660172, input); // Vị trí mặc định nếu không hỗ trợ định vị
    }

    document.getElementById('suggestions').innerHTML = '';
}

function showSuggestions() {
    const input = document.getElementById('search-input').value.toLowerCase();
    const suggestions = document.getElementById('suggestions');
    suggestions.innerHTML = '';

    if (input === '') {
        return;
    }

    const filteredLots = parking_lots.filter(lot => 
        lot.name.toLowerCase().includes(input) || 
        lot.location.toLowerCase().includes(input)
    );

    filteredLots.forEach(lot => {
        const suggestionItem = document.createElement('div');
        suggestionItem.classList.add('suggestion-item');
        suggestionItem.innerText = lot.name;
        suggestionItem.onclick = () => {
            document.getElementById('search-input').value = lot.name;
            searchParkingLots();
            suggestions.innerHTML = '';
        };
        suggestions.appendChild(suggestionItem);
    });
}

function getDirections(lat, lng) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const currentLat = position.coords.latitude;
            const currentLng = position.coords.longitude;
            window.open(`https://www.google.com/maps/dir/?api=1&origin=${currentLat},${currentLng}&destination=${lat},${lng}`);
        });
    } else {
        alert('Trình duyệt của bạn không hỗ trợ định vị vị trí.');
    }
}

document.getElementById('search-input').addEventListener('focus', () => {
    // Lấy vị trí hiện tại nếu có sẵn
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;

            // Sắp xếp các bãi đỗ theo khoảng cách từ vị trí hiện tại của người dùng
            parking_lots.sort((a, b) => {
                const distanceA = calculateDistance(userLat, userLng, a.latitude, a.longitude);
                const distanceB = calculateDistance(userLat, userLng, b.latitude, b.longitude);
                return distanceA - distanceB;
            });

            // Hiển thị 5 bãi đỗ gần nhất trong gợi ý
            const suggestions = document.getElementById('suggestions');
            suggestions.innerHTML = '';
            for (let i = 0; i < 5 && i < parking_lots.length; i++) {
                const suggestionItem = document.createElement('div');
                suggestionItem.classList.add('suggestion-item');
                suggestionItem.innerText = parking_lots[i].name;
                suggestionItem.onclick = () => {
                    document.getElementById('search-input').value = parking_lots[i].name;
                    searchParkingLots();
                    suggestions.innerHTML = '';
                };
                suggestions.appendChild(suggestionItem);
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', initMap);
