package main

import (
	"bufio"
	"crypto/rand"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// ==============================================================================
// УТИЛИТЫ И ЗАПУСК КОМАНД
// ==============================================================================

// runCmd запускает внешнюю команду в указанной директории.
// dir — рабочая папка, name — программа, args — аргументы.
func runCmd(dir string, name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}

// dc — обертка для вызова docker compose с указанием абсолютного пути к файлу.
func dc(projectDir string, check bool, args ...string) bool {
	composeFile := filepath.Join(projectDir, "docker-compose.yml")
	fullArgs := append([]string{"compose", "-f", composeFile}, args...)
	err := runCmd(projectDir, "docker", fullArgs...)
	if err != nil && check {
		fmt.Printf("\n[ERROR] Команда завершилась с ошибкой: %v\n", err)
		return false
	}
	return true
}

// generatePassword создает случайный пароль заданной длины.
func generatePassword(length int) string {
	const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	result := make([]byte, length)
	for i := range result {
		num, _ := rand.Int(rand.Reader, big.NewInt(int64(len(chars))))
		result[i] = chars[num.Int64()]
	}
	return string(result)
}

// updateEnv обновляет или добавляет переменные в файл .env.
func updateEnv(filePath string, updates map[string]string) {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return
	}
	lines := strings.Split(string(content), "\n")
	var newLines []string
	updated := make(map[string]bool)

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if strings.Contains(line, "=") && !strings.HasPrefix(trimmed, "#") {
			parts := strings.SplitN(line, "=", 2)
			key := strings.TrimSpace(parts[0])
			if val, ok := updates[key]; ok {
				newLines = append(newLines, fmt.Sprintf("%s=%s", key, val))
				updated[key] = true
				continue
			}
		}
		newLines = append(newLines, line)
	}

	for k, v := range updates {
		if !updated[k] {
			newLines = append(newLines, fmt.Sprintf("%s=%s", k, v))
		}
	}

	finalContent := strings.Join(newLines, "\n")
	if !strings.HasSuffix(finalContent, "\n") {
		finalContent += "\n"
	}
	os.WriteFile(filePath, []byte(finalContent), 0644)
}

// regenLock пересобирает uv.lock внутри временного контейнера (если изменился pyproject.toml).
func regenLock(projectDir string) {
	backendPath := filepath.Join(projectDir, "backend")
	if _, err := os.Stat(filepath.Join(backendPath, "pyproject.toml")); os.IsNotExist(err) {
		fmt.Println("[WARN] Не найден backend/pyproject.toml, пропускаю пересборку uv.lock.")
		return
	}

	fmt.Println("\n[INFO] Пересборка uv.lock (обновление зависимостей)...")
	err := runCmd(projectDir, "docker", "run", "--rm",
		"-v", fmt.Sprintf("%s:/app", backendPath),
		"-w", "/app",
		"-e", "UV_PROJECT_ENVIRONMENT=/tmp/uv-venv",
		"python:3.12-slim",
		"sh", "-c", "pip install --quiet uv==0.5.11 && uv lock")

	if err != nil {
		fmt.Println("[WARN] Не удалось обновить uv.lock. Сборка может упасть.")
	} else {
		fmt.Println("[OK] uv.lock успешно обновлен.")
	}
}

// ==============================================================================
// ПЕРВИЧНАЯ НАСТРОЙКА
// ==============================================================================

func setupEnv(projectDir string) bool {
	envPath := filepath.Join(projectDir, ".env")
	examplePath := filepath.Join(projectDir, ".env.example")

	if _, err := os.Stat(envPath); err == nil {
		fmt.Println("[INFO] Файл .env уже существует. Сохраняю текущие настройки.")
		return false
	}

	fmt.Println("[INFO] Создание нового .env с безопасным паролем...")
	password := generatePassword(24)
	content, err := os.ReadFile(examplePath)
	if err != nil {
		fmt.Println("[ERROR] Не найден файл .env.example")
		return false
	}
	
	newContent := strings.Replace(string(content), "DB_USER=", "DB_USER=conturai_user", 1)
	newContent = strings.Replace(newContent, "DB_PASSWORD=", "DB_PASSWORD="+password, 1)
	
	os.WriteFile(envPath, []byte(newContent), 0644)
	return true
}

func pickPlatform(projectDir string) {
	fmt.Println("\nВыберите платформу:")
	fmt.Println("  1) NVIDIA (CUDA)")
	fmt.Println("  2) AMD (ROCm)")
	fmt.Println("  3) CPU")
	fmt.Print("Номер [1]: ")
	
	reader := bufio.NewReader(os.Stdin)
	choice, _ := reader.ReadString('\n')
	choice = strings.TrimSpace(choice)
	if choice == "" { choice = "1" }

	mode := "nvidia"
	if choice == "2" { mode = "amd" } else if choice == "3" { mode = "cpu" }

	src := filepath.Join(projectDir, "templates", fmt.Sprintf("docker-compose.%s.yml", mode))
	dst := filepath.Join(projectDir, "docker-compose.yml")

	data, err := os.ReadFile(src)
	if err != nil {
		fmt.Printf("[ERROR] Не найден шаблон %s\n", src)
		return
	}
	os.WriteFile(dst, data, 0644)
	fmt.Printf("[OK] Конфигурация Docker настроена для %s\n", mode)

	envPath := filepath.Join(projectDir, ".env")
	updates := map[string]string{}
	if mode == "nvidia" {
		updates["PYTORCH_INDEX"] = "https://download.pytorch.org/whl/cu121"
		updates["VLLM_IMAGE"] = "vllm/vllm-openai:latest"
	} else if mode == "amd" {
		updates["PYTORCH_INDEX"] = "https://download.pytorch.org/whl/rocm6.1"
		updates["VLLM_IMAGE"] = "rocm/vllm:latest"
	} else {
		updates["PYTORCH_INDEX"] = "https://download.pytorch.org/whl/cpu"
		updates["VLLM_IMAGE"] = "vllm/vllm-openai-cpu:latest"
	}
	updateEnv(envPath, updates)
}

func pickModel(projectDir string) {
	fmt.Println("\nВыберите модель ИИ:")
	fmt.Println("  1) Qwen2.5-0.5B (CPU / слабый ПК)")
	fmt.Println("  2) Qwen2.5-1.5B (8-12 ГБ VRAM)")
	fmt.Println("  3) Qwen2.5-3B   (16 ГБ VRAM)")
	fmt.Println("  4) Qwen2.5-7B   (24+ ГБ VRAM)")
	fmt.Println("  5) Своя модель (HuggingFace ID)")
	fmt.Print("Номер [2]: ")

	reader := bufio.NewReader(os.Stdin)
	choice, _ := reader.ReadString('\n')
	choice = strings.TrimSpace(choice)
	if choice == "" { choice = "2" }

	var mName, mFile, maxLen string

	if choice == "5" {
		fmt.Print("Введите HuggingFace repo_id (Автор/Название): ")
		repoID, _ := reader.ReadString('\n')
		repoID = strings.TrimSpace(repoID)
		parts := strings.Split(repoID, "/")
		mFile = parts[len(parts)-1]
		mName = repoID
		fmt.Print("Максимальная длина контекста [4096]: ")
		maxLen, _ = reader.ReadString('\n')
		maxLen = strings.TrimSpace(maxLen)
		if maxLen == "" { maxLen = "4096" }
	} else {
		models := map[string][3]string{
			"1": {"Qwen/Qwen2.5-0.5B-Instruct", "Qwen2.5-0.5B-Instruct", "2048"},
			"2": {"Qwen/Qwen2.5-1.5B-Instruct", "Qwen2.5-1.5B-Instruct", "2048"},
			"3": {"Qwen/Qwen2.5-3B-Instruct", "Qwen2.5-3B-Instruct", "4096"},
			"4": {"Qwen/Qwen2.5-7B-Instruct", "Qwen2.5-7B-Instruct", "8192"},
		}
		m := models[choice]
		if m[0] == "" { m = models["2"] }
		mName, mFile, maxLen = m[0], m[1], m[2]
	}

	envPath := filepath.Join(projectDir, ".env")
	updateEnv(envPath, map[string]string{
		"VLLM_MODEL_PATH": fmt.Sprintf("/models/%s", mFile),
		"VLLM_MAX_MODEL_LEN": maxLen,
		"MODELS_TO_DOWNLOAD": fmt.Sprintf("intfloat/multilingual-e5-large:multilingual-e5-large,BAAI/bge-reranker-v2-m3:bge-reranker-v2-m3,%s:%s", mName, mFile),
	})
	fmt.Printf("[OK] Выбрана модель: %s\n", mFile)
}

// ==============================================================================
// БИЗНЕС-ЛОГИКА (УСТАНОВКА, ОБНОВЛЕНИЕ, ПЕРЕУСТАНОВКА)
// ==============================================================================

func doInstall(projectDir string) {
	isNew := setupEnv(projectDir)
	if isNew {
		pickPlatform(projectDir)
		pickModel(projectDir)
	}

	regenLock(projectDir)

	fmt.Println("\n[INFO] Запуск сборки контейнеров (это может занять время)...")
	dc(projectDir, false, "down", "--remove-orphans")
	if !dc(projectDir, true, "up", "-d", "--build") {
		return
	}

	fmt.Println("\n[INFO] Ожидание инициализации базы данных (15 секунд)...")
	time.Sleep(15 * time.Second)

	fmt.Println("\n[INFO] Инициализация схемы БД...")
	dc(projectDir, false, "exec", "-T", "backend", "python", "scripts/manage.py", "init-db")
	
	fmt.Println("\n[INFO] Создание администратора...")
	dc(projectDir, false, "exec", "-T", "backend", "python", "scripts/manage.py", "reset-admin")

	fmt.Println("\n[SUCCESS] Установка завершена! Откройте http://localhost:3000")
}

func doUpdate(projectDir string) {
	if _, err := os.Stat(filepath.Join(projectDir, ".env")); os.IsNotExist(err) {
		fmt.Println("[ERROR] Файл .env не найден. Сначала выполните Установку.")
		return
	}

	fmt.Println("\n[INFO] Обновление сервера и базы данных...")
	regenLock(projectDir)

	dc(projectDir, false, "down", "--remove-orphans")
	if !dc(projectDir, true, "up", "-d", "--build") {
		return
	}

	fmt.Println("\n[INFO] Ожидание запуска БД...")
	time.Sleep(15 * time.Second)

	fmt.Println("\n[INFO] Применение миграций БД...")
	dc(projectDir, false, "exec", "-T", "backend", "python", "scripts/manage.py", "migrate")

	fmt.Println("\n[SUCCESS] Обновление завершено!")
}

func doFullReinstall(projectDir string) {
	fmt.Print("\n[WARN] ВНИМАНИЕ! Это удалит все данные, БД и .env. Продолжить? (y/N): ")
	reader := bufio.NewReader(os.Stdin)
	confirm, _ := reader.ReadString('\n')
	if strings.ToLower(strings.TrimSpace(confirm)) != "y" {
		return
	}

	fmt.Println("[INFO] Удаление контейнеров и томов...")
	dc(projectDir, false, "down", "-v", "--remove-orphans")

	os.Remove(filepath.Join(projectDir, ".env"))
	doInstall(projectDir)
}

// ==============================================================================
// ИНТЕРАКТИВНЫЕ МЕНЮ
// ==============================================================================

func menuContainers(projectDir string) {
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Println("\n--- Управление контейнерами ---")
		fmt.Println("  1) Запустить (up -d)")
		fmt.Println("  2) Остановить (stop)")
		fmt.Println("  3) Перезапустить (restart)")
		fmt.Println("  4) Пересобрать (up -d --build)")
		fmt.Println("  5) Остановить и удалить (down)")
		fmt.Println("  6) Логи (logs -f)")
		fmt.Println("  0) Назад")
		fmt.Print("Номер [0]: ")
		c, _ := reader.ReadString('\n')
		c = strings.TrimSpace(c)

		switch c {
		case "1": dc(projectDir, true, "up", "-d")
		case "2": dc(projectDir, true, "stop")
		case "3": dc(projectDir, true, "restart")
		case "4": dc(projectDir, true, "up", "-d", "--build")
		case "5": dc(projectDir, true, "down", "--remove-orphans")
		case "6": 
			fmt.Println("[INFO] Нажмите Ctrl+C для выхода из логов.")
			dc(projectDir, false, "logs", "-f")
		case "0": return
		}
	}
}

func menuManage(projectDir string) {
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Println("\n--- Команды manage.py ---")
		fmt.Println("  1) init-db (Создать таблицы)")
		fmt.Println("  2) reset-admin (Сбросить пароль админа)")
		fmt.Println("  3) migrate (Применить миграции)")
		fmt.Println("  4) download-models (Скачать модели)")
		fmt.Println("  5) reembed (Переиндексация RAG)")
		fmt.Println("  6) backup (Резервная копия)")
		fmt.Println("  0) Назад")
		fmt.Print("Номер [0]: ")
		c, _ := reader.ReadString('\n')
		c = strings.TrimSpace(c)

		switch c {
		case "1": dc(projectDir, true, "exec", "-T", "backend", "python", "scripts/manage.py", "init-db")
		case "2": dc(projectDir, true, "exec", "-T", "backend", "python", "scripts/manage.py", "reset-admin")
		case "3": dc(projectDir, true, "exec", "-T", "backend", "python", "scripts/manage.py", "migrate")
		case "4": 
			fmt.Println("[INFO] Запуск скачивания (через отдельный контейнер)...")
			dc(projectDir, true, "run", "--rm", "--no-deps", "-e", "HF_HUB_OFFLINE=0", "-e", "TRANSFORMERS_OFFLINE=0", "-e", "HF_DATASETS_OFFLINE=0", "backend", "python", "scripts/manage.py", "download-models")
		case "5": dc(projectDir, true, "exec", "-T", "backend", "python", "scripts/manage.py", "reembed")
		case "6": dc(projectDir, true, "exec", "-T", "backend", "python", "scripts/manage.py", "backup")
		case "0": return
		}
	}
}

// ==============================================================================
// ТОЧКА ВХОДА
// ==============================================================================

func main() {
	fmt.Println("==================================================")
	fmt.Println("  ConturAI - Универсальный установщик")
	fmt.Println("==================================================")

	// 1. Проверка Docker
	if err := runCmd(".", "docker", "info"); err != nil {
		fmt.Println("\n[ERROR] Docker не запущен или не установлен.")
		fmt.Println("Запустите Docker Desktop и повторите попытку.")
		os.Exit(1)
	}

	// 2. Умный поиск корня проекта
	// Если exe лежит в папке bin/, то корень проекта — это двумя уровнями выше.
	// Если exe лежит прямо в корне, то корень — это папка с exe.
	exePath, _ := os.Executable()
	dirOfExe := filepath.Dir(exePath)
	
	projectDir := dirOfExe
	// Проверяем, есть ли docker-compose.yml в папке с exe
	if _, err := os.Stat(filepath.Join(projectDir, "docker-compose.yml")); os.IsNotExist(err) {
		// Если нет, поднимаемся на уровень выше (из bin/ в корень)
		projectDir = filepath.Dir(dirOfExe)
	}

	// Дополнительная проверка на всякий случай
	if _, err := os.Stat(filepath.Join(projectDir, "docker-compose.yml")); os.IsNotExist(err) {
		fmt.Printf("\n[WARN] Не удалось автоматически найти docker-compose.yml.\n")
		fmt.Printf("Установщик ожидает, что файлы проекта лежат в папке: %s\n", projectDir)
	}

	reader := bufio.NewReader(os.Stdin)

	for {
		fmt.Printf("\nГлавное меню (Проект: %s)\n", projectDir)
		fmt.Println("  1) Установка с нуля")
		fmt.Println("  2) Обновление (сохранить данные)")
		fmt.Println("  3) Полная переустановка (сброс БД)")
		fmt.Println("  4) Управление контейнерами")
		fmt.Println("  5) Команды manage.py")
		fmt.Println("  0) Выход")
		fmt.Print("Номер [1]: ")
		
		choice, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(choice)
		if choice == "" { choice = "1" }

		switch choice {
		case "1": doInstall(projectDir)
		case "2": doUpdate(projectDir)
		case "3": doFullReinstall(projectDir)
		case "4": menuContainers(projectDir)
		case "5": menuManage(projectDir)
		case "0": 
			fmt.Println("До свидания!")
			return
		}
	}
}