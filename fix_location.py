import re

js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# We use regex to find the whole initializeAgriSathi function block
pattern = r'async function initializeAgriSathi\(\) \{.*?\n\}'

new_func = '''async function initializeAgriSathi() {
    applyLanguage();
    applyTheme();
    loadSavedLocation();
    updateCharacterCount();

    elements.verificationStatus.textContent = "Waiting for your question";
    
    await checkBackend();

    // AUTO-LOCATION LOGIC
    if (!state.location) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    try {
                        // Free reverse geocoding API
                        const geoResponse = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`);
                        const geoData = await geoResponse.json();
                        
                        const city = geoData.city || geoData.locality || geoData.principalSubdivision;
                        if (city) {
                            elements.locationInput.value = city;
                            state.location = city;
                            localStorage.setItem("agrisathi.location", city);
                            showToast(`Auto-detected location: ${city}`);
                            await loadWeather();
                        }
                    } catch (error) {
                        console.log("Reverse geocoding failed, user can type manually.");
                    }
                },
                (error) => {
                    console.log("Location permission denied. User can type manually.");
                }
            );
        }
    } else {
        // If location is already saved, load weather immediately
        await loadWeather();
    }
}'''

if re.search(pattern, js, flags=re.DOTALL):
    js = re.sub(pattern, new_func, js, flags=re.DOTALL)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print('✅ Auto-Location (GPS) successfully added!')
else:
    print('⚠️ Could not find the initialize function via Regex. Please check script.js.')
