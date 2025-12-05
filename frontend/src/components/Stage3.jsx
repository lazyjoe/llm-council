import ReactMarkdown from 'react-markdown';
import './Stage3.css';

export default function Stage3({ finalResponse, onRetry, isRetrying }) {
  if (!finalResponse) {
    return null;
  }

  const hasError = finalResponse.response?.startsWith('Error:');

  return (
    <div className={`stage stage3 ${hasError ? 'error-state' : ''}`}>
      <h3 className="stage-title">Stage 3: Final Council Answer</h3>
      <div className="final-response">
        <div className="chairman-label">
          Chairman: {finalResponse.model.split('/')[1] || finalResponse.model}
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>

        {hasError && onRetry && (
          <div className="retry-container">
            <button
              className="retry-button"
              onClick={onRetry}
              disabled={isRetrying}
            >
              {isRetrying ? 'Retrying Stage 3...' : 'Retry Stage 3'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
