import axios from 'axios';

// VITE_API_URL will be set in Vercel later.
// If it's missing, it defaults to localhost (for you).
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const fetchCafes = async (lat, lng) => {
    try {
        const response = await axios.get(`${API_URL}/cafes`, {
            params: { lat, lng, radius_km: 5, limit: 50 }
        });
        return response.data;
    } catch (error) {
        console.error("Error fetching cafes:", error);
        return [];
    }
};