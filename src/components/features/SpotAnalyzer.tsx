import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Camera, Upload, Zap, MapPin, Eye, AlertCircle, BarChart3 } from 'lucide-react'

export default function SpotAnalyzer() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [usageStats, setUsageStats] = useState<any>(null)
  const [provider, setProvider] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select a valid image file')
        return
      }
      
      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        setError('Image too large. Please select an image under 10MB')
        return
      }
      
      setError(null)
      setSelectedFile(file)
      
      const reader = new FileReader()
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string)
        setAnalysis(null)
      }
      reader.readAsDataURL(file)
    }
  }

  const fetchUsageStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/usage-stats')
      const result = await response.json()
      if (result.success) {
        setUsageStats(result.usage)
      }
    } catch (error) {
      console.error('Failed to fetch usage stats:', error)
    }
  }

  const analyzeSpot = async (endpoint: string = 'analyze-smart') => {
    if (!selectedFile) return
    
    setLoading(true)
    setError(null)
    
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      const response = await fetch(`http://localhost:8000/${endpoint}`, {
        method: 'POST',
        body: formData,
      })
      
      const result = await response.json()
      
      if (result.success) {
        setAnalysis(result.recommendation)
        setProvider(result.provider)
        // Fetch updated usage stats
        await fetchUsageStats()
      } else {
        setError(result.error || 'Analysis failed')
      }
    } catch (error) {
      console.error('Analysis error:', error)
      setError('Failed to analyze image. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const resetAnalyzer = () => {
    setSelectedImage(null)
    setSelectedFile(null)
    setAnalysis(null)
    setError(null)
    setProvider('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Fetch usage stats on component mount
  React.useEffect(() => {
    fetchUsageStats()
  }, [])

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-3xl font-bold text-white mb-4">
          AI Spot Analyzer
        </h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Upload a photo of your fishing spot and get AI-powered recommendations 
          on where to cast, what bait to use, and the best fishing techniques.
        </p>
      </motion.div>

      {/* Usage Stats */}
      {usageStats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-5 w-5 text-accent-orange" />
              <span className="text-white font-medium">Google AI Usage Today</span>
            </div>
            <div className="text-right">
              <div className="text-white font-bold">
                {usageStats.daily.used}/{usageStats.daily.limit}
              </div>
              <div className="text-sm text-gray-400">
                {usageStats.daily.percentage.toFixed(1)}% used
              </div>
            </div>
          </div>
          <div className="mt-2 bg-gray-700 rounded-full h-2">
            <div 
              className="bg-accent-orange rounded-full h-2 transition-all duration-300"
              style={{ width: `${Math.min(usageStats.daily.percentage, 100)}%` }}
            />
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Image Upload Section */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">
            Upload Fishing Spot Photo
          </h2>
          
          <div className="space-y-4">
            {!selectedImage ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-600 rounded-xl p-8 text-center cursor-pointer hover:border-accent-orange transition-colors"
              >
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-400 mb-2">
                  Click to upload or drag and drop
                </p>
                <p className="text-sm text-gray-500">
                  PNG, JPG, GIF up to 10MB
                </p>
              </div>
            ) : (
              <div className="relative">
                <img
                  src={selectedImage}
                  alt="Fishing spot"
                  className="w-full h-64 object-cover rounded-xl"
                />
                <button
                  onClick={resetAnalyzer}
                  className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                >
                  ×
                </button>
              </div>
            )}
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
            
            {error && (
              <div className="flex items-center space-x-2 p-3 bg-red-900/20 border border-red-800 rounded-lg">
                <AlertCircle className="h-4 w-4 text-red-400" />
                <span className="text-red-400 text-sm">{error}</span>
              </div>
            )}
            
            <div className="space-y-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary w-full"
              >
                <Camera className="h-4 w-4 mr-2" />
                Choose Photo
              </button>
              
              {selectedImage && (
                <div className="grid grid-cols-1 gap-2">
                  <button
                    onClick={() => analyzeSpot('analyze-smart')}
                    disabled={loading}
                    className="btn-primary disabled:opacity-50"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin h-4 w-4 mr-2 border-2 border-white border-t-transparent rounded-full" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 mr-2" />
                        Smart Analysis (Best Quality)
                      </>
                    )}
                  </button>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => analyzeSpot('analyze-gemini')}
                      disabled={loading}
                      className="btn-secondary text-xs disabled:opacity-50"
                    >
                      Gemini Direct
                    </button>
                    <button
                      onClick={() => analyzeSpot('analyze-hf')}
                      disabled={loading}
                      className="btn-secondary text-xs disabled:opacity-50"
                    >
                      HF Fallback
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Analysis Results */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">
              AI Analysis Results
            </h2>
            {provider && (
              <span className="text-xs bg-accent-orange px-2 py-1 rounded-full text-white">
                {provider}
              </span>
            )}
          </div>
          
          {!analysis && !loading ? (
            <div className="text-center py-12">
              <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-400">
                Upload a photo to get AI-powered fishing recommendations
              </p>
            </div>
          ) : loading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-2 border-accent-orange border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-400">
                Analyzing your fishing spot...
              </p>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <div className="bg-gray-700/50 rounded-xl p-4 border border-gray-600 max-h-96 overflow-y-auto">
                <div className="whitespace-pre-line text-sm text-gray-300 leading-relaxed">
                  {analysis}
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button className="btn-primary flex-1">
                  <MapPin className="h-4 w-4 mr-2" />
                  Save Location
                </button>
                <button className="btn-secondary">
                  Share Results
                </button>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Tips Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="card p-6"
      >
        <h2 className="text-xl font-semibold text-white mb-4">
          Photography Tips for Better Analysis
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4">
            <div className="w-12 h-12 bg-accent-blue rounded-xl flex items-center justify-center mx-auto mb-3">
              <Camera className="h-6 w-6 text-white" />
            </div>
            <h3 className="font-medium text-white mb-2">Clear Water View</h3>
            <p className="text-sm text-gray-400">
              Capture the water surface and any visible underwater structure
            </p>
          </div>
          
          <div className="text-center p-4">
            <div className="w-12 h-12 bg-accent-green rounded-xl flex items-center justify-center mx-auto mb-3">
              <MapPin className="h-6 w-6 text-white" />
            </div>
            <h3 className="font-medium text-white mb-2">Include Shoreline</h3>
            <p className="text-sm text-gray-400">
              Show vegetation, rocks, and other shoreline features
            </p>
          </div>
          
          <div className="text-center p-4">
            <div className="w-12 h-12 bg-accent-orange rounded-xl flex items-center justify-center mx-auto mb-3">
              <Eye className="h-6 w-6 text-white" />
            </div>
            <h3 className="font-medium text-white mb-2">Good Lighting</h3>
            <p className="text-sm text-gray-400">
              Take photos during daylight for best structure visibility
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}