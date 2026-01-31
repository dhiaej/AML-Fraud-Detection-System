import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Adjust the base URL as needed

export const detectFraud = async (userId: string) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/detect-fraud/${userId}`);
        return response.data;
    } catch (error) {
        console.error('Error detecting fraud:', error);
        throw error;
    }
};