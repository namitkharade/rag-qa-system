import { useEffect, useRef, useState } from 'react';

const JsonEditor = ({ sessionId, onJsonUpdate }) => {
  const [jsonText, setJsonText] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [parsedData, setParsedData] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    const exampleData = [
      {
        type: 'POLYLINE',
        layer: 'Plot Boundary',
        points: [
          [-13160.59, 19584.96],
          [-3160.59, 19584.96],
          [-3160.59, 44584.96],
          [-13160.59, 44584.96],
        ],
        closed: true,
      },
      {
        type: 'POLYLINE',
        layer: 'Walls',
        points: [
          [-9660.59, 29584.96],
          [-10660.59, 29584.96],
          [-10660.59, 22084.96],
          [-8560.59, 22084.96],
          [-8560.59, 29584.96],
        ],
        closed: true,
      },
    ];
    setJsonText(JSON.stringify(exampleData, null, 2));
    setParsedData(exampleData);
  }, []);

  const handleJsonChange = (e) => {
    const text = e.target.value;
    setJsonText(text);

    try {
      const parsed = JSON.parse(text);
      setIsValid(true);
      setErrorMessage('');
      setParsedData(parsed);
    } catch (error) {
      setIsValid(false);
      setErrorMessage(error.message);
      setParsedData(null);
    }
  };

  const handleApplyJson = () => {
    if (isValid && parsedData) {
      onJsonUpdate(parsedData);
    }
  };

  const handleClearJson = () => {
    setJsonText('{}');
    setParsedData({});
    setUploadedFileName('');
    onJsonUpdate(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check if it's a JSON file
    if (!file.name.endsWith('.json')) {
      setIsValid(false);
      setErrorMessage('Please upload a valid JSON file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target.result;
        const parsed = JSON.parse(text);
        
        setJsonText(JSON.stringify(parsed, null, 2));
        setParsedData(parsed);
        setIsValid(true);
        setErrorMessage('');
        setUploadedFileName(file.name);
      } catch (error) {
        setIsValid(false);
        setErrorMessage(`Error parsing JSON file: ${error.message}`);
        setUploadedFileName('');
      }
    };

    reader.onerror = () => {
      setIsValid(false);
      setErrorMessage('Error reading file');
      setUploadedFileName('');
    };

    reader.readAsText(file);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800">
          JSON Editor
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Architectural drawing (ephemeral data - not stored in Vector DB)
        </p>
        {uploadedFileName && (
          <p className="text-xs text-blue-600 mt-2 font-medium flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            Loaded: {uploadedFileName}
          </p>
        )}
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden p-4">
        {/* Upload Button */}
        <div className="mb-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            onClick={handleUploadClick}
            className="w-full px-4 py-2 bg-blue-50 text-blue-700 border-2 border-dashed border-blue-300 rounded-lg hover:bg-blue-100 hover:border-blue-400 transition-colors flex items-center justify-center gap-2 text-sm font-medium"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            Upload JSON File
          </button>
        </div>
        
        <textarea
          value={jsonText}
          onChange={handleJsonChange}
          className={`w-full h-full font-mono text-sm p-3 border rounded-lg focus:outline-none focus:ring-2 ${
            isValid
              ? 'border-gray-300 focus:ring-primary'
              : 'border-red-500 focus:ring-red-500'
          }`}
          placeholder="Upload a JSON file or paste your architectural drawing JSON here..."
          spellCheck="false"
        />
      </div>

      {/* Status */}
      <div className="p-4 border-t border-gray-200">
        {!isValid && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            <strong>Invalid JSON:</strong> {errorMessage}
          </div>
        )}

        {isValid && parsedData && (
          <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
            Valid JSON ({Object.keys(parsedData).length} keys)
          </div>
        )}

        <div className="flex space-x-2">
          <button
            onClick={handleApplyJson}
            disabled={!isValid || !sessionId}
            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Apply to Session
          </button>
          <button
            onClick={handleClearJson}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  );
};

export default JsonEditor;
