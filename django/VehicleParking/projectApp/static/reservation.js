console.log("hello world");

document.addEventListener("DOMContentLoaded", function() {
    const parkingLotId = window.parkingLotId;

    function updateParkingSpots() {
        fetch(`/api/parking_spots/${parkingLotId}/`)
            .then(response => response.json())
            .then(data => {
                const spots = data.spots;
                const totalAvailableSpots = data.total_available_spots;

                document.getElementById(`availability-${parkingLotId}`).textContent = totalAvailableSpots;

                spots.forEach(spot => {
                    const button = document.querySelector(`.btn-spot[data-spot-id="${spot.id}"]`);
                    if (spot.is_reserved || !spot.is_avaiable) {
                        button.classList.remove('available');
                        button.classList.add('reserved');
                        button.disabled = true;
                    } else {
                        button.classList.remove('reserved');
                        button.classList.add('available');
                        button.disabled = false;
                    }
                });
            })
            .catch(error => console.error('Error fetching parking spots:', error));
    }

    // Gọi hàm updateParkingSpots khi trang được tải
    updateParkingSpots();

    // Tạo một interval để cập nhật vị trí đỗ mỗi 5 giây
    setInterval(updateParkingSpots, 5000);
});


// static/app.js

let map;
let markers = [];
let parkingLots = [];

function initMap() {
    map = L.map('map').setView([10.762622, 106.660172], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            fetch(`/api/parking_lots/?latitude=${userLat}&longitude=${userLng}&search=${window.parkingLotName}`)
                .then(response => response.json())
                .then(data => {
                    parkingLots = data;
                    data.forEach(lot => {
                        addMarker(lot);
                    });
                    markers.forEach(item => {
                        item.marker.setOpacity(1); // Show marker
                        map.setView(item.marker.getLatLng(), 14);
                        item.marker.openPopup(); // Open the marker's popup
                    });
                });
        });
    } else {
        // loadParkingLots(10.762622, 106.660172); // Default location if geolocation is not supported
    }
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

function calculatePrice() {
    const reservedFrom = document.getElementById('id_reserved_from').value;
    const reservedTo = document.getElementById('id_reserved_to').value;
    const priceFirstTwoHours = window.parkingLotPriceFirstTwoHours;
    const pricePerHourAfterTwoHours = window.parkingLotPricePerHourAfterTwoHours;
    const totalPriceElement = document.getElementById('total-price');

    if (reservedFrom && reservedTo) {
        // Chuyển đổi chuỗi thời gian thành đối tượng Date
        const fromTimeParts = reservedFrom.split(':');
        const toTimeParts = reservedTo.split(':');
        
        const fromDate = new Date();
        fromDate.setHours(parseInt(fromTimeParts[0], 10), parseInt(fromTimeParts[1], 10), 0, 0);
        
        const toDate = new Date();
        toDate.setHours(parseInt(toTimeParts[0], 10), parseInt(toTimeParts[1], 10), 0, 0);
        
        const totalHours = Math.abs(toDate - fromDate) / 36e5; // 36e5 là số mili giây trong một giờ
        const roundedHours = Math.ceil(totalHours); // Làm tròn lên
        if (roundedHours <= 2)
            totalPrice = 1 * priceFirstTwoHours
        else 
            totalPrice = (1 * priceFirstTwoHours) + ((roundedHours - 2) * pricePerHourAfterTwoHours)
        
            
        
        totalPriceElement.textContent = `${totalPrice.toLocaleString()} VND`;
    } else {
        totalPriceElement.textContent = '0 VND';
    }
}


document.addEventListener('DOMContentLoaded', initMap);
