class Imgmeta < Formula
  include Language::Python::Virtualenv

  desc "Personal CLI tool for extracting, exporting, and removing EXIF metadata from photos"
  homepage "https://github.com/polidisio/exiftool-cli"
  url "https://github.com/polidisio/exiftool-cli.git",
      tag: "v1.0.0",
      revision: "0000000000000000000000000000000000000000"
  license "MIT"
  head "https://github.com/polidisio/exiftool-cli.git", branch: "main"

  depends_on "python@3.11"
  depends_on "pillow"
  depends_on "piexif"
  depends_on "click"
  depends_on "colorama"

  def install
    virtualenv_created_with_system_python = false

    args = ["--no-download", "--withoutensurepip"]
    if OS.mac?
      args << "--with-system-python"
    end

    venv = virtualenv_create(libexec, "python3.11", *args)
    venv.pip_install_and_link(buildpath)

    bin.install_symlink "#{libexec}/bin/imgmeta" => "imgmeta"
  end

  test do
    system "#{bin}/imgmeta", "--version"
  end
end
