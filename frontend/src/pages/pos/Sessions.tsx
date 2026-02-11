import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { computersApi, sessionsApi } from '../../api/computers';
import { Computer, Session } from '../../types';
import { ArrowLeft, Monitor, Play, Square } from 'lucide-react';

const Sessions: React.FC = () => {
    const [computers, setComputers] = useState<Computer[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const loadData = async () => {
        try {
            const [computersData, sessionsData] = await Promise.all([
                computersApi.list(),
                sessionsApi.list(true),
            ]);
            setComputers(computersData);
            setSessions(sessionsData);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    };

    const handleStartSession = async (computerId: string) => {
        try {
            await sessionsApi.start(computerId);
            loadData();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to start session');
        }
    };

    const handleStopSession = async (sessionId: string) => {
        try {
            await sessionsApi.stop(sessionId);
            loadData();
            alert('Session stopped successfully');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to stop session');
        }
    };

    const getSessionForComputer = (computerId: string) => {
        return sessions.find((s) => s.computer_id === computerId);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'available':
                return 'bg-green-100 text-green-800 border-green-200';
            case 'in_use':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'offline':
                return 'bg-gray-100 text-gray-800 border-gray-200';
            case 'maintenance':
                return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center gap-4">
                        <Link to="/pos" className="btn btn-secondary">
                            <ArrowLeft className="w-4 h-4" />
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-900">Computer Sessions</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {computers.map((computer) => {
                        const session = getSessionForComputer(computer.id);
                        const duration = session
                            ? Math.floor((new Date().getTime() - new Date(session.start_time).getTime()) / 60000)
                            : 0;

                        return (
                            <div key={computer.id} className={`card border-2 ${getStatusColor(computer.status)}`}>
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <Monitor className="w-8 h-8" />
                                        <div>
                                            <h3 className="text-lg font-semibold">{computer.name}</h3>
                                            <p className="text-sm capitalize">{computer.status.replace('_', ' ')}</p>
                                        </div>
                                    </div>
                                </div>

                                {session && (
                                    <div className="mb-4 p-3 bg-white rounded-lg">
                                        <p className="text-sm text-gray-600">Duration</p>
                                        <p className="text-2xl font-bold">{duration} min</p>
                                        <p className="text-sm text-gray-600 mt-2">
                                            Started: {new Date(session.start_time).toLocaleTimeString()}
                                        </p>
                                    </div>
                                )}

                                {computer.status === 'available' ? (
                                    <button
                                        onClick={() => handleStartSession(computer.id)}
                                        className="w-full btn btn-primary flex items-center justify-center gap-2"
                                    >
                                        <Play className="w-4 h-4" />
                                        Start Session
                                    </button>
                                ) : computer.status === 'in_use' && session ? (
                                    <button
                                        onClick={() => handleStopSession(session.id)}
                                        className="w-full btn btn-danger flex items-center justify-center gap-2"
                                    >
                                        <Square className="w-4 h-4" />
                                        Stop Session
                                    </button>
                                ) : null}
                            </div>
                        );
                    })}
                </div>
            </main>
        </div>
    );
};

export default Sessions;
