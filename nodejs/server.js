const http = require('http');
const server = http.createServer();
const axios = require('axios');
const qs = require('qs');
const socketio = require('socket.io');
const io = socketio(server, {
    cors: {
        origin: 'https://wiggle22.pythonanywhere.com',
        methods: ['GET', 'POST']
    }
});
const { Board, Leds, Sensor, LCD } = require("johnny-five");

// Global arrays to store state information
let sensors = [];
let sensorsWithOne = [];
let sensorStates = Array(10).fill(0);
let lcd = null;
let leds = null;

// Initialize the board
new Board({ port: "COM4" }).on("ready", function() {
    console.log("Johnny-Five board is ready!");

    leds = new Leds([27, 29, 31, 33, 35, 37, 39, 41, 43, 45]);

    for (let i = 26; i <= 44; i += 2) {
        sensors[i / 2 - 13] = new Sensor.Digital({
            pin: i
        });
        sensors[i / 2 - 13].on("change", onChangeCallback.bind(null, leds[i / 2 - 13], i / 2 - 13)); 
    }

    // Initialize LCD
    lcd = new LCD({
        controller: "PCF8574T"
    });

    // Update the LCD with initial state
    updateLCD(); 

    io.on('connection', onConnection);
    const PORT = process.env.PORT || 3000; // Use process.env.PORT or default to 3000
    server.listen(PORT, () => console.log(`listening on port ${PORT}`));
});

function updateLCD(index) {
    if (!lcd) return;
    const emptySpots = sensorStates
        .map((value, i) => value === 1 ? i : null)
        .filter(i => i !== null).length;
    lcd.cursor(0, 0).print(`So cho trong: ${emptySpots} `);
    if (index === undefined) {
        // Update the entire LCD screen
        lcd.useChar("check");
        lcd.cursor(1, 0);

        sensorStates.forEach((state, i) => {
            const ledState = state === 0 ? "X" : (state === 1 ? ":check:" : "O");
            lcd.print(`${i+1}: ${ledState} `);

            // Move to the next line after every 4 LEDs 
            if ((i+1) % 4 === 0 && (i+1) !== sensorStates.length - 1) {
                lcd.cursor(Math.floor((i+1) / 4) + 1, 0);
            }
        });
    } else {
        // Update only the changed position on the LCD
        lcd.useChar("check");
        const ledIndex = index;
        const state = sensorStates[index];
        const ledState = state === 0 ? "X" : (state === 1 ? ":check:" : "O");
        const row = Math.floor(ledIndex / 4) + 1;
        const col = (ledIndex % 4) * 5; // Assuming each led state takes 4 columns

        lcd.cursor(row, col).print(`${ledIndex + 1}: ${ledState} `);
    }
}

function onChangeCallback(led, index, value) {
    if (value === 0) {
        led.on();
    } else {
        led.off();
    }

    sensorStates[index] = value;
    sensorsWithOne = sensorStates
        .map((value, i) => value === 1 ? i : null)
        .filter(i => i !== null);

    const isLotFull = sensorStates.every(value => value === 0);
    const data = qs.stringify({ lot_id: 1, is_available: isLotFull ? 'full' : 'not full', sensorsWithOne: JSON.stringify(sensorsWithOne) });
    axios.post('https://wiggle22.pythonanywhere.com/api/update-availability/', data, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
        .then(response => {
            console.log('Phản hồi từ Django:', response.data);
        })
        .catch(error => {
            console.error('Lỗi khi gửi yêu cầu đến Django:', error);
        });

    // Update the LCD when a change occurs
    updateLCD(index);
}

function onConnection(socket) {
    console.log('connected');
    socket.on('update_reserved_spots', onUpdateReservedSpots);
    socket.on('cancel_reserved_spots', offUpdateReservedSpots);
}

function onUpdateReservedSpots(data) {
    const { lot_id, spot_numbers } = data;
    console.log('Dat:', data)
    // Cập nhật trạng thái của các vị trí được đặt
    spot_numbers.forEach(spot_number => {
        sensorStates[spot_number - 1] = 2; // Cập nhật trạng thái là 2 cho vị trí được đặt 
        
        // Bật LED tương ứng với vị trí được đặt
        leds[spot_number - 1].on();

        // Cập nhật LCD   
        updateLCD(spot_number - 1);
    });
}

function offUpdateReservedSpots(data) {
    const { lot_id, spot_numbers } = data;
    console.log('Huy:', data)
    // Cập nhật trạng thái của các vị trí được đặt
    spot_numbers.forEach(spot_number => {
        sensorStates[spot_number - 1] = 1; // Cập nhật trạng thái là 2 cho vị trí được đặt 
        
        // Bật LED tương ứng với vị trí được đặt
        leds[spot_number - 1].off();

        // Cập nhật LCD   
        updateLCD(spot_number - 1);
    });
}

process.on('exit', () => {
    sensors = null;
    sensorsWithOne = null;
    sensorStates = null;
});
