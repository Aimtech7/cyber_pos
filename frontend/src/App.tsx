import React from 'react';
import './index.css';

function App() {
    return (
        <div className="p-10 text-center">
            <h1 className="text-3xl font-bold text-green-600">Frontend is Working!</h1>
            <p className="mt-4">If you see this, the React mount is successful.</p>
            <p className="mt-2 text-sm text-gray-500">Backend Status: Running on port 8000</p>
        </div>
    );
}

export default App;
