import { useEffect, useState } from 'react';

const JsonEditor = ({ sessionId, onJsonUpdate }) => {
  const [jsonText, setJsonText] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [parsedData, setParsedData] = useState(null);

  useEffect(() => {
    const exampleData = {
      building_name: 'Office Building A',
      floors: 5,
      total_area: 15000,
      occupancy_type: 'Business',
      features: {
        fire_exits: 4,
        sprinkler_system: true,
        emergency_lighting: true,
      },
      zones: [
        { id: 'zone_1', type: 'office', area: 8000 },
        { id: 'zone_2', type: 'common', area: 3000 },
        { id: 'zone_3', type: 'mechanical', area: 4000 },
      ],
    };
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
    onJsonUpdate(null);
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
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden p-4">
        <textarea
          value={jsonText}
          onChange={handleJsonChange}
          className={`w-full h-full font-mono text-sm p-3 border rounded-lg focus:outline-none focus:ring-2 ${
            isValid
              ? 'border-gray-300 focus:ring-primary'
              : 'border-red-500 focus:ring-red-500'
          }`}
          placeholder="Enter your architectural drawing JSON here..."
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
