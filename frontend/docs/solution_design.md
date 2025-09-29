# Frontend Application - Solution Design

## Application Overview

**Purpose**: React TypeScript frontend for Resume Match Pro AI  
**Technology**: React 18 with TypeScript  
**Deployment**: Vercel/Netlify (free tier)  
**Architecture**: Single Page Application (SPA)  

## Technology Stack

### Core Framework
- **React**: 18.x with TypeScript
- **Build Tool**: Vite (fast development and builds)
- **Package Manager**: npm/yarn
- **State Management**: Zustand (lightweight alternative to Redux)
- **Routing**: React Router v6

### UI/UX Libraries
- **Styling**: Tailwind CSS
- **Components**: Headless UI (unstyled, accessible components)
- **Icons**: Heroicons or Lucide React
- **Drag & Drop**: react-dropzone
- **File Upload**: Custom implementation with progress tracking

### Authentication & Data
- **Auth**: Supabase Auth client
- **API Client**: Axios with interceptors
- **Form Handling**: React Hook Form with Zod validation
- **File Handling**: Native File API with drag-drop support

## Project Structure

```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   ├── layout/          # Layout components
│   │   ├── documents/       # Document-related components
│   │   ├── matching/        # Matching and search components
│   │   └── auth/            # Authentication components
│   ├── pages/
│   │   ├── Dashboard.tsx    # Main dashboard page
│   │   ├── Login.tsx        # Login page
│   │   ├── Register.tsx     # Registration page
│   │   └── Settings.tsx     # User settings
│   ├── hooks/
│   │   ├── useAuth.ts       # Authentication hook
│   │   ├── useDocuments.ts  # Document management hook
│   │   ├── useMatching.ts   # Matching functionality hook
│   │   └── useSearch.ts     # Search functionality hook
│   ├── services/
│   │   ├── api.ts           # API client configuration
│   │   ├── auth.ts          # Authentication service
│   │   ├── documents.ts     # Document service
│   │   └── matching.ts      # Matching service
│   ├── types/
│   │   ├── auth.ts          # Authentication types
│   │   ├── document.ts      # Document types
│   │   ├── matching.ts      # Matching types
│   │   └── api.ts           # API response types
│   ├── utils/
│   │   ├── constants.ts     # Application constants
│   │   ├── helpers.ts       # Utility functions
│   │   └── validation.ts    # Validation schemas
│   ├── store/
│   │   ├── authStore.ts     # Authentication state
│   │   ├── documentStore.ts # Document state
│   │   └── uiStore.ts       # UI state
│   ├── styles/
│   │   ├── globals.css      # Global styles
│   │   └── components.css   # Component-specific styles
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Application entry point
│   └── vite-env.d.ts        # Vite type definitions
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── .env.example
```

## Key Features Implementation

### 1. Authentication Flow
```typescript
// useAuth hook
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email, password
    })
    if (error) throw error
    return data
  }

  const signInWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google'
    })
    if (error) throw error
    return data
  }
}
```

### 2. Dual-Pane Layout
```typescript
// Dashboard component structure
const Dashboard = () => {
  return (
    <div className="flex h-screen">
      <DocumentPanel 
        type="cv" 
        documents={cvs}
        onDocumentClick={handleCVClick}
        onUpload={handleCVUpload}
      />
      <DocumentPanel 
        type="job_description" 
        documents={jobDescriptions}
        onDocumentClick={handleJDClick}
        onUpload={handleJDUpload}
      />
    </div>
  )
}
```

### 3. Drag & Drop Upload
```typescript
// useDocumentUpload hook
export const useDocumentUpload = () => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      const formData = new FormData()
      formData.append('file', file)
      
      // Upload with progress tracking
      uploadDocument(formData, {
        onUploadProgress: (progress) => {
          setUploadProgress(progress.loaded / progress.total * 100)
        }
      })
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    }
  })
}
```

### 4. Real-time Search & Filtering
```typescript
// useSearch hook with debouncing
export const useSearch = () => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const debouncedSearch = useMemo(
    () => debounce(async (searchQuery: string) => {
      if (!searchQuery.trim()) return
      
      setLoading(true)
      try {
        const response = await api.post('/search/semantic', {
          query: searchQuery,
          filters: { /* current filters */ }
        })
        setResults(response.data.results)
      } finally {
        setLoading(false)
      }
    }, 300),
    []
  )

  useEffect(() => {
    debouncedSearch(query)
  }, [query, debouncedSearch])
}
```

## State Management (Zustand)

### Authentication Store
```typescript
interface AuthState {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  session: null,
  loading: true,
  // ... implementation
}))
```

### Document Store
```typescript
interface DocumentState {
  cvs: Document[]
  jobDescriptions: Document[]
  selectedCV: Document | null
  selectedJD: Document | null
  uploadProgress: Record<string, number>
  fetchDocuments: () => Promise<void>
  uploadDocument: (file: File, type: DocumentType) => Promise<void>
  deleteDocument: (id: string) => Promise<void>
}
```

## API Integration

### API Client Setup
```typescript
// services/api.ts
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 30000,
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().signOut()
    }
    return Promise.reject(error)
  }
)
```

## Performance Optimization

### Code Splitting
```typescript
// Lazy loading for routes
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Settings = lazy(() => import('./pages/Settings'))

// Route configuration
const router = createBrowserRouter([
  {
    path: "/dashboard",
    element: <Suspense fallback={<LoadingSpinner />}><Dashboard /></Suspense>
  }
])
```

### Caching Strategy
```typescript
// React Query for server state caching
export const useDocuments = () => {
  return useQuery({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  })
}
```

## Responsive Design

### Tailwind Breakpoints
```typescript
// Mobile-first responsive design
<div className="
  flex flex-col          // Mobile: stack vertically
  lg:flex-row           // Desktop: side by side
  h-screen
">
  <DocumentPanel className="
    w-full               // Mobile: full width
    lg:w-1/2            // Desktop: half width
    h-1/2               // Mobile: half height
    lg:h-full           // Desktop: full height
  " />
</div>
```

## Error Handling

### Error Boundary
```typescript
class ErrorBoundary extends Component {
  state = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    // Send to error tracking service
  }
}
```

### Toast Notifications
```typescript
// Global toast system for user feedback
export const useToast = () => {
  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    toast(message, { type })
  }
  return { showToast }
}
```

## Testing Strategy

### Component Testing
```typescript
// Jest + React Testing Library
describe('DocumentPanel', () => {
  it('should handle file drop', async () => {
    const onUpload = jest.fn()
    render(<DocumentPanel onUpload={onUpload} />)
    
    const dropzone = screen.getByTestId('dropzone')
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    
    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })
    
    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledWith(file)
    })
  })
})
```

## Deployment Configuration

### Vercel Deployment
```json
// vercel.json
{
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### Environment Variables
```bash
# .env.example
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
REACT_APP_API_URL=your_api_gateway_url
```

## Security Considerations

### Content Security Policy
```typescript
// Helmet configuration
<Helmet>
  <meta httpEquiv="Content-Security-Policy" content="
    default-src 'self';
    script-src 'self' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    connect-src 'self' https://your-supabase-url.supabase.co;
  " />
</Helmet>
```

### Input Sanitization
```typescript
// Zod validation schemas
export const documentUploadSchema = z.object({
  file: z.instanceof(File)
    .refine(file => file.size <= 5 * 1024 * 1024, 'File too large')
    .refine(file => ['application/pdf', 'application/msword'].includes(file.type), 'Invalid file type')
})
```

This frontend architecture provides a modern, performant, and cost-effective solution that integrates seamlessly with the backend services while maintaining excellent user experience for HR professionals.




