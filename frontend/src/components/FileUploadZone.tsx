import React, { useCallback, useState } from 'react';
import { Upload, X, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploadTask {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
  maxSizeMB?: number;
}

export function FileUploadZone({ 
  onFilesSelected, 
  maxFiles = 10,
  acceptedTypes = ['.pdf'],
  maxSizeMB = 50 
}: FileUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [tasks, setTasks] = useState<UploadTask[]>([]);

  const handleFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const validFiles: File[] = [];
    const newTasks: UploadTask[] = [];

    fileArray.forEach((file) => {
      if (validFiles.length >= maxFiles) return;
      
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedTypes.includes(ext)) {
        return;
      }
      
      if (file.size > maxSizeMB * 1024 * 1024) {
        return;
      }

      validFiles.push(file);
      newTasks.push({
        id: Math.random().toString(36).substr(2, 9),
        file,
        progress: 0,
        status: 'pending',
      });
    });

    if (validFiles.length > 0) {
      setTasks(prev => [...prev, ...newTasks]);
      onFilesSelected(validFiles);
    }
  }, [maxFiles, acceptedTypes, maxSizeMB, onFilesSelected]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
    e.target.value = '';
  }, [handleFiles]);

  const removeTask = (id: string) => {
    setTasks(prev => prev.filter(t => t.id !== id));
  };

  return (
    <div className="space-y-4">
      <div
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
          isDragOver 
            ? "border-primary bg-primary/5" 
            : "border-muted-foreground/25 hover:border-primary/50"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-upload-input')?.click()}
      >
        <Upload className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
        <p className="text-sm font-medium mb-1">
          Drag & drop files here or click to browse
        </p>
        <p className="text-xs text-muted-foreground">
          PDF files up to {maxSizeMB}MB (max {maxFiles} files)
        </p>
        <input
          id="file-upload-input"
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          className="hidden"
          onChange={handleFileInput}
        />
      </div>

      {tasks.length > 0 && (
        <div className="space-y-2">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg"
            >
              <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{task.file.name}</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full transition-all",
                        task.status === 'error' ? 'bg-destructive' :
                        task.status === 'success' ? 'bg-green-500' :
                        'bg-primary'
                      )}
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground w-12 text-right">
                    {task.progress}%
                  </span>
                </div>
              </div>
              <div className="shrink-0">
                {task.status === 'success' && (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
                {task.status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-destructive" title={task.error} />
                )}
                {task.status === 'pending' || task.status === 'uploading' ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeTask(task.id);
                    }}
                    className="p-1 hover:bg-destructive/10 rounded"
                  >
                    <X className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
