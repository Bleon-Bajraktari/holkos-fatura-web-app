import { useState, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface PasswordInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'ref'> {
  containerClassName?: string;
  inputClassName?: string;
}

const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordInput({ containerClassName = '', inputClassName = '', className, ...props }, ref) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className={`relative ${containerClassName}`}>
      <input
        ref={ref}
        type={showPassword ? 'text' : 'password'}
        className={`pr-12 ${inputClassName || className || ''}`}
        {...props}
      />
      <button
        type="button"
        onClick={() => setShowPassword(!showPassword)}
        className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
        tabIndex={-1}
        aria-label={showPassword ? 'Fshih fjalëkalimin' : 'Shfaq fjalëkalimin'}
      >
        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
});

export default PasswordInput;
