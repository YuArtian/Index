import axios from 'axios'

export const request = axios.create({
  baseURL: 'http://localhost:8000',
})

request.interceptors.request.use((config) => {
  config.headers['Content-Type'] ??= 'application/json'
  return config
})

request.interceptors.response.use(
  (res) => res.data,
  (error) => {
    if (error.name === 'CanceledError') return Promise.reject(error)
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  },
)
